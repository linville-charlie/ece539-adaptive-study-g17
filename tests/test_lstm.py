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
"""Check that training and prediction use only earlier answers."""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from types import SimpleNamespace

import torch

from ece539_adaptive_study_g17.prediction.lstm_data import (
    LSTMPredictor,
    collate_samples,
    make_samples,
    make_vocabs,
    split_learners,
)
from ece539_adaptive_study_g17.prediction.lstm_model import LSTMErrorModel
from ece539_adaptive_study_g17.prediction.train_lstm import train_lstm


@dataclass(frozen=True)
class Interaction:
    learner_id: str
    interaction_id: str
    question_id: str
    concept_ids: tuple[str, ...]
    subject_id: str
    timestamp_ms: int
    response_time_ms: int | None
    correct: bool


def extract_features(
    history: Sequence[Interaction], _concept_id: str, _timestamp_ms: int
) -> SimpleNamespace:
    values = (0.0, float(history[-1].correct) if history else 0.0) + (0.0,) * 10
    mask = (bool(history),) * 12
    return SimpleNamespace(values=values, observed_mask=mask)


def test_target_answer_is_not_in_its_input() -> None:
    earlier = Interaction("learner", "a1", "q1", ("a",), "math", 1000, 300, True)
    target = Interaction("learner", "a2", "q2", ("a",), "math", 2000, 400, False)
    concepts, subjects = make_vocabs([earlier, target])
    original = make_samples([earlier, target], concepts, subjects, extract_features)[1]
    changed = replace(target, correct=True, response_time_ms=999)
    updated = make_samples([earlier, changed], concepts, subjects, extract_features)[1]

    assert torch.equal(original.features, updated.features)
    assert torch.equal(original.history_concept_ids, updated.history_concept_ids)
    assert original.error == 1
    assert updated.error == 0

    changed_history = make_samples(
        [replace(earlier, correct=False), target],
        concepts,
        subjects,
        extract_features,
    )[1]
    assert not torch.equal(original.features, changed_history.features)


def test_multi_tag_attempt_has_one_total_weight() -> None:
    target = Interaction("learner", "a1", "q1", ("a", "b"), "math", 1000, None, False)
    concepts, subjects = make_vocabs([target])
    samples = make_samples([target], concepts, subjects, extract_features)

    expected_samples = 2
    assert len(samples) == expected_samples
    assert [sample.error for sample in samples] == [1, 1]
    assert sum(sample.weight for sample in samples) == 1
    assert collate_samples(samples)[0].shape == (2, 1, 27)


def test_past_skill_ids_and_answers_are_in_sequence() -> None:
    first = Interaction("learner", "a1", "q1", ("a", "b"), "math", 1000, 300, False)
    second = Interaction("learner", "a2", "q2", ("b",), "math", 2000, None, True)
    target = Interaction("learner", "a3", "q3", ("a",), "math", 3000, 400, False)
    concepts, subjects = make_vocabs([first, second, target])
    sample = make_samples(
        [first, second, target], concepts, subjects, extract_features
    )[-1]

    assert sample.history_concept_ids.tolist() == [[1, 2], [2, 0], [0, 0]]
    assert sample.features[:, -3].tolist() == [0.0, 1.0, 0.0]
    assert sample.features[:, -1].tolist() == [1.0, 0.0, 0.0]
    assert sample.features[0, -2] > 0


def test_learner_split_is_disjoint() -> None:
    rows = [
        Interaction(str(i), str(i), "q", ("a",), "math", 1000, None, True)
        for i in range(20)
    ]
    train, dev, test = split_learners(rows)
    assert (len(train), len(dev), len(test)) == (14, 3, 3)
    assert {row.learner_id for row in train}.isdisjoint(
        row.learner_id for row in dev + test
    )


def test_predictor_scores_candidate_concepts() -> None:
    history = [Interaction("learner", "a1", "q1", ("a",), "math", 1000, 300, True)]
    concepts, subjects = make_vocabs(history)
    model = LSTMErrorModel(len(concepts) + 1, len(subjects) + 1)
    predictor = LSTMPredictor(model, concepts, subjects, extract_features)
    request = SimpleNamespace(
        history=history,
        concept_id="a",
        subject_id="math",
        prediction_timestamp_ms=2000,
        feature_vector=extract_features(history, "a", 2000),
    )
    assert 0 <= predictor.predict_error(request) <= 1
    request.concept_id = "new"
    request.subject_id = "new subject"
    assert 0 <= predictor.predict_error(request) <= 1


def test_training_uses_prepared_batches() -> None:
    rows = [
        Interaction("learner", "a1", "q1", ("a",), "math", 1000, 300, True),
        Interaction("learner", "a2", "q2", ("a",), "math", 2000, 400, False),
    ]
    concepts, subjects = make_vocabs(rows)
    model = LSTMErrorModel(len(concepts) + 1, len(subjects) + 1)
    batch = collate_samples(make_samples(rows, concepts, subjects, extract_features))

    epochs = 2
    losses = train_lstm(model, [batch], epochs=epochs)
    assert len(losses) == epochs
    assert all(loss >= 0 for loss in losses)
