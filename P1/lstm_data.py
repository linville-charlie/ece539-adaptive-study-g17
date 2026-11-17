"""Prepare P2 response histories for the LSTM."""
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from math import log1p
from random import Random

import torch
from torch.nn.utils.rnn import pad_sequence

from non_neural import (
    FEATURE_NAMES, FeatureVector, Interaction, PredictionRequest,
    extract_features, to_feature_vector,
)
from lstm_model import LSTMErrorModel


TIME_FEATURES = {
    "previous_response_time", "time_since_previous_interaction",
    "time_since_last_skill_attempt", "skill_avg_response_time",
    "recent_skill_avg_response_time",
}
COUNT_FEATURES = {
    "skill_attempt_count", "skill_correct_streak", "overall_attempt_count",
}


def feature_row(vector: FeatureVector) -> torch.Tensor:
    values = []
    for name, value, observed in zip(
        FEATURE_NAMES, vector.values, vector.observed_mask,
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


def feature_sequence(
    history: Sequence[Interaction], concept_id: str, timestamp_ms: int,
    concept_vocab: dict[str, int], max_length: int = 50,
    target_vector: FeatureVector | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Keep past attempts in order and leave the target answer out."""
    if max_length < 1:
        raise ValueError("max_length must be positive")
    prior = sorted(
        (row for row in history if row.timestamp_ms < timestamp_ms),
        key=lambda row: row.timestamp_ms,
    )
    start = max(0, len(prior) - max_length + 1)
    events = prior[start:]
    rows = []
    for index, event in enumerate(events, start):
        earlier = prior[:index]
        context = feature_row(to_feature_vector(
            extract_features(earlier, concept_id, event.timestamp_ms)
        ))
        duration = event.response_time_ms
        answer = torch.tensor([
            float(event.correct),
            log1p(duration / 1000) if duration is not None else 0.0,
            float(duration is not None),
        ])
        rows.append(torch.cat((context, answer)))
    if target_vector is None:
        target_vector = to_feature_vector(
            extract_features(prior, concept_id, timestamp_ms)
        )
    rows.append(torch.cat((feature_row(target_vector), torch.zeros(3))))
    tag_count = max((len(event.concept_ids) for event in events), default=1)
    ids = torch.zeros((len(rows), tag_count), dtype=torch.long)
    for index, event in enumerate(events):
        ids[index, :len(event.concept_ids)] = torch.tensor(
            [concept_vocab.get(tag, 0) for tag in event.concept_ids]
        )
    return torch.stack(rows), ids


def split_learners(
    interactions: Sequence[Interaction], seed: int = 0,
) -> tuple[list[Interaction], list[Interaction], list[Interaction]]:
    """Split learners 70/15/15 so their histories stay in one group."""
    learners = sorted({row.learner_id for row in interactions})
    Random(seed).shuffle(learners)
    train_end = round(0.7 * len(learners))
    dev_end = round(0.85 * len(learners))
    groups = (
        set(learners[:train_end]), set(learners[train_end:dev_end]),
        set(learners[dev_end:]),
    )
    return tuple(
        [row for row in interactions if row.learner_id in group]
        for group in groups
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
    interactions: Sequence[Interaction], concept_vocab: dict[str, int],
    subject_vocab: dict[str, int], max_length: int = 50,
) -> list[LSTMSample]:
    by_learner = defaultdict(list)
    for row in interactions:
        by_learner[row.learner_id].append(row)

    samples = []
    for learner_rows in by_learner.values():
        ordered = sorted(learner_rows, key=lambda row: row.timestamp_ms)
        for index, target in enumerate(ordered):
            for concept_id in target.concept_ids:
                features, history_ids = feature_sequence(
                    ordered[:index], concept_id, target.timestamp_ms,
                    concept_vocab, max_length,
                )
                samples.append(LSTMSample(
                    features=features,
                    history_concept_ids=history_ids,
                    concept_id=concept_vocab.get(concept_id, 0),
                    subject_id=subject_vocab.get(target.subject_id, 0),
                    error=float(not target.correct),
                    weight=1 / len(target.concept_ids),
                ))
    return samples


def collate_samples(samples: list[LSTMSample]) -> tuple[torch.Tensor, ...]:
    max_length = max(len(sample.features) for sample in samples)
    max_tags = max(sample.history_concept_ids.shape[1] for sample in samples)
    history_ids = torch.zeros(
        (len(samples), max_length, max_tags), dtype=torch.long,
    )
    for index, sample in enumerate(samples):
        ids = sample.history_concept_ids
        history_ids[index, :len(ids), :ids.shape[1]] = ids
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
    """Use P2's prediction request to score one candidate concept."""

    def __init__(
        self, model: LSTMErrorModel, concept_vocab: dict[str, int],
        subject_vocab: dict[str, int], max_length: int = 50,
    ) -> None:
        self.model = model
        self.concept_vocab = concept_vocab
        self.subject_vocab = subject_vocab
        self.max_length = max_length

    def predict_error(self, request: PredictionRequest) -> float:
        features, history_ids = feature_sequence(
            request.history, request.concept_id, request.prediction_timestamp_ms,
            self.concept_vocab, self.max_length, request.feature_vector,
        )
        device = next(self.model.parameters()).device
        probability = self.model.predict_error_batch(
            features.unsqueeze(0).to(device),
            history_ids.unsqueeze(0).to(device),
            torch.tensor([len(features)]),
            torch.tensor(
                [self.concept_vocab.get(request.concept_id, 0)], device=device,
            ),
            torch.tensor(
                [self.subject_vocab.get(request.subject_id, 0)], device=device,
            ),
        )
        return probability.item()
