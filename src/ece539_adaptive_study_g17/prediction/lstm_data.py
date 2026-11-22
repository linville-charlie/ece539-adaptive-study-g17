#   539g17 Adaptive Study Integration Project
#   Copyright (C) 2026  A. Kancherla, C. Linville, Q. Schultz, E. Wulf.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Authors of this file:
#
# - Charlie Linville
#
# This file header was last modified 21 Nov 2026.
"""Prepare learner response histories for the LSTM."""

from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import log1p
from random import Random
from typing import Protocol

import torch
from torch.nn.utils.rnn import pad_sequence

from ece539_adaptive_study_g17.prediction.lstm_model import LSTMErrorModel

FEATURE_NAMES = (
    "previous_response_time",
    "previous_correct",
    "time_since_previous_interaction",
    "time_since_last_skill_attempt",
    "skill_attempt_count",
    "skill_avg_response_time",
    "skill_accuracy",
    "recent_skill_avg_response_time",
    "recent_skill_accuracy",
    "skill_correct_streak",
    "overall_accuracy",
    "overall_attempt_count",
)


class Interaction(Protocol):
    """An answered attempt in one learner's history."""

    learner_id: str
    concept_ids: tuple[str, ...]
    subject_id: str
    timestamp_ms: int
    response_time_ms: int | None
    correct: bool


class FeatureVector(Protocol):
    """The 12 historical features and their observation mask."""

    values: tuple[float, ...]
    observed_mask: tuple[bool, ...]


class PredictionRequest(Protocol):
    """A target concept and the learner's earlier attempts."""

    history: Sequence[Interaction]
    concept_id: str
    subject_id: str
    prediction_timestamp_ms: int
    feature_vector: FeatureVector


FeatureExtractor = Callable[[Sequence[Interaction], str, int], FeatureVector]


TIME_FEATURES = {
    "previous_response_time",
    "time_since_previous_interaction",
    "time_since_last_skill_attempt",
    "skill_avg_response_time",
    "recent_skill_avg_response_time",
}
COUNT_FEATURES = {
    "skill_attempt_count",
    "skill_correct_streak",
    "overall_attempt_count",
}


def feature_row(vector: FeatureVector) -> torch.Tensor:
    """Scale historical values and append their observation mask."""
    if len(vector.values) != len(FEATURE_NAMES) or len(vector.observed_mask) != len(
        FEATURE_NAMES
    ):
        raise ValueError("features")
    values = []
    for name, value, observed in zip(
        FEATURE_NAMES,
        vector.values,
        vector.observed_mask,
        strict=True,
    ):
        if not observed:
            values.append(0.0)
        elif name in TIME_FEATURES:
            values.append(log1p(value / 1000))
        elif name in COUNT_FEATURES:
            values.append(log1p(value))
        else:
            values.append(value)
    values.extend(float(observed) for observed in vector.observed_mask)
    return torch.tensor(values, dtype=torch.float32)


@dataclass(frozen=True)
class SequenceConfig:
    """The vocabulary, feature source, and history length."""

    concept_vocab: dict[str, int]
    feature_extractor: FeatureExtractor
    max_length: int = 50


def feature_sequence(
    history: Sequence[Interaction],
    concept_id: str,
    timestamp_ms: int,
    config: SequenceConfig,
    target_vector: FeatureVector | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Keep past attempts in order and leave the target answer out."""
    if config.max_length < 1:
        raise ValueError("max_length")
    prior = sorted(
        (row for row in history if row.timestamp_ms < timestamp_ms),
        key=lambda row: row.timestamp_ms,
    )
    start = max(0, len(prior) - config.max_length + 1)
    events = prior[start:]
    rows = []
    for index, event in enumerate(events, start):
        earlier = prior[:index]
        context = feature_row(
            config.feature_extractor(earlier, concept_id, event.timestamp_ms)
        )
        duration = event.response_time_ms
        answer = torch.tensor(
            [
                float(event.correct),
                log1p(duration / 1000) if duration is not None else 0.0,
                float(duration is not None),
            ]
        )
        rows.append(torch.cat((context, answer)))
    if target_vector is None:
        target_vector = config.feature_extractor(prior, concept_id, timestamp_ms)
    rows.append(torch.cat((feature_row(target_vector), torch.zeros(3))))
    tag_count = max((len(event.concept_ids) for event in events), default=1)
    ids = torch.zeros((len(rows), tag_count), dtype=torch.long)
    for index, event in enumerate(events):
        ids[index, : len(event.concept_ids)] = torch.tensor(
            [config.concept_vocab.get(tag, 0) for tag in event.concept_ids]
        )
    return torch.stack(rows), ids


def split_learners(
    interactions: Sequence[Interaction],
    seed: int = 0,
) -> tuple[list[Interaction], list[Interaction], list[Interaction]]:
    """Split learners 70/15/15 so their histories stay in one group."""
    learners = sorted({row.learner_id for row in interactions})
    Random(seed).shuffle(learners)
    train_end = round(0.7 * len(learners))
    dev_end = round(0.85 * len(learners))
    groups = (
        set(learners[:train_end]),
        set(learners[train_end:dev_end]),
        set(learners[dev_end:]),
    )
    return (
        [row for row in interactions if row.learner_id in groups[0]],
        [row for row in interactions if row.learner_id in groups[1]],
        [row for row in interactions if row.learner_id in groups[2]],
    )


def make_vocabs(
    interactions: Sequence[Interaction],
) -> tuple[dict[str, int], dict[str, int]]:
    """Build training ID maps, reserving zero for unseen IDs."""
    concepts = sorted({concept for row in interactions for concept in row.concept_ids})
    subjects = sorted({row.subject_id for row in interactions})
    return (
        {concept: index + 1 for index, concept in enumerate(concepts)},
        {subject: index + 1 for index, subject in enumerate(subjects)},
    )


@dataclass
class LSTMSample:
    """A target answer paired with its earlier history."""

    features: torch.Tensor
    history_concept_ids: torch.Tensor
    concept_id: int
    subject_id: int
    error: float
    weight: float


def make_samples(
    interactions: Sequence[Interaction],
    concept_vocab: dict[str, int],
    subject_vocab: dict[str, int],
    feature_extractor: FeatureExtractor,
    max_length: int = 50,
) -> list[LSTMSample]:
    """Make one training target per concept tag on each attempt."""
    by_learner = defaultdict(list)
    for row in interactions:
        by_learner[row.learner_id].append(row)

    samples = []
    config = SequenceConfig(concept_vocab, feature_extractor, max_length)
    for learner_rows in by_learner.values():
        ordered = sorted(learner_rows, key=lambda row: row.timestamp_ms)
        for index, target in enumerate(ordered):
            for concept_id in target.concept_ids:
                features, history_ids = feature_sequence(
                    ordered[:index],
                    concept_id,
                    target.timestamp_ms,
                    config,
                )
                samples.append(
                    LSTMSample(
                        features=features,
                        history_concept_ids=history_ids,
                        concept_id=concept_vocab.get(concept_id, 0),
                        subject_id=subject_vocab.get(target.subject_id, 0),
                        error=float(not target.correct),
                        weight=1 / len(target.concept_ids),
                    )
                )
    return samples


def collate_samples(samples: list[LSTMSample]) -> tuple[torch.Tensor, ...]:
    """Pad samples and return one batch of tensors."""
    max_length = max(len(sample.features) for sample in samples)
    max_tags = max(sample.history_concept_ids.shape[1] for sample in samples)
    history_ids = torch.zeros(
        (len(samples), max_length, max_tags),
        dtype=torch.long,
    )
    for index, sample in enumerate(samples):
        ids = sample.history_concept_ids
        history_ids[index, : len(ids), : ids.shape[1]] = ids
    return (
        pad_sequence([sample.features for sample in samples], batch_first=True),
        history_ids,
        torch.tensor([len(sample.features) for sample in samples]),
        torch.tensor([sample.concept_id for sample in samples]),
        torch.tensor([sample.subject_id for sample in samples]),
        torch.tensor([sample.error for sample in samples]),
        torch.tensor([sample.weight for sample in samples]),
    )


class LSTMPredictor:
    """Predict the chance of a wrong answer for the requested concept."""

    def __init__(
        self,
        model: LSTMErrorModel,
        concept_vocab: dict[str, int],
        subject_vocab: dict[str, int],
        feature_extractor: FeatureExtractor,
        max_length: int = 50,
    ) -> None:
        """Set up the model and its training vocabulary."""
        self.model = model
        self.concept_vocab = concept_vocab
        self.subject_vocab = subject_vocab
        self.config = SequenceConfig(concept_vocab, feature_extractor, max_length)

    def predict_error(self, request: PredictionRequest) -> float:
        """Return the error probability for one candidate concept."""
        features, history_ids = feature_sequence(
            request.history,
            request.concept_id,
            request.prediction_timestamp_ms,
            self.config,
            request.feature_vector,
        )
        device = next(self.model.parameters()).device
        probability = self.model.predict_error_batch(
            features.unsqueeze(0).to(device),
            history_ids.unsqueeze(0).to(device),
            torch.tensor([len(features)]),
            torch.tensor(
                [self.concept_vocab.get(request.concept_id, 0)],
                device=device,
            ),
            torch.tensor(
                [self.subject_vocab.get(request.subject_id, 0)],
                device=device,
            ),
        )
        return probability.item()
