"""Check that training and prediction use only earlier answers."""
from dataclasses import replace

import torch

from non_neural import (
    CandidateConcept, ConceptSelector, InMemoryAttemptRepository, Interaction,
)
from lstm_data import (
    LSTMPredictor, collate_samples, make_samples, make_vocabs, split_learners,
)
from lstm_model import LSTMErrorModel
from train_lstm import train_lstm


def test_target_answer_is_not_in_its_input():
    earlier = Interaction('learner', 'a1', 'q1', ('a',), 'math', 1000, 300, True)
    target = Interaction('learner', 'a2', 'q2', ('a',), 'math', 2000, 400, False)
    concepts, subjects = make_vocabs([earlier, target])
    original = make_samples([earlier, target], concepts, subjects)[1]
    changed = replace(target, correct=True, response_time_ms=999)
    updated = make_samples([earlier, changed], concepts, subjects)[1]

    assert torch.equal(original.features, updated.features)
    assert torch.equal(original.history_concept_ids, updated.history_concept_ids)
    assert original.error == 1
    assert updated.error == 0

    changed_history = make_samples(
        [replace(earlier, correct=False), target], concepts, subjects
    )[1]
    assert not torch.equal(original.features, changed_history.features)


def test_multi_tag_attempt_has_one_total_weight():
    target = Interaction('learner', 'a1', 'q1', ('a', 'b'), 'math', 1000, None, False)
    concepts, subjects = make_vocabs([target])
    samples = make_samples([target], concepts, subjects)

    assert len(samples) == 2
    assert [sample.error for sample in samples] == [1, 1]
    assert sum(sample.weight for sample in samples) == 1
    assert collate_samples(samples)[0].shape == (2, 1, 27)


def test_past_skill_ids_and_answers_are_in_sequence():
    first = Interaction('learner', 'a1', 'q1', ('a', 'b'), 'math', 1000, 300, False)
    second = Interaction('learner', 'a2', 'q2', ('b',), 'math', 2000, None, True)
    target = Interaction('learner', 'a3', 'q3', ('a',), 'math', 3000, 400, False)
    concepts, subjects = make_vocabs([first, second, target])
    sample = make_samples([first, second, target], concepts, subjects)[-1]

    assert sample.history_concept_ids.tolist() == [[1, 2], [2, 0], [0, 0]]
    assert sample.features[:, -3].tolist() == [0.0, 1.0, 0.0]
    assert sample.features[:, -1].tolist() == [1.0, 0.0, 0.0]
    assert sample.features[0, -2] > 0


def test_learner_split_is_disjoint():
    rows = [
        Interaction(str(i), str(i), 'q', ('a',), 'math', 1000, None, True)
        for i in range(20)
    ]
    train, dev, test = split_learners(rows)
    assert (len(train), len(dev), len(test)) == (14, 3, 3)
    assert set(row.learner_id for row in train).isdisjoint(
        row.learner_id for row in dev + test
    )


def test_selector_receives_model_error_probability():
    history = [Interaction('learner', 'a1', 'q1', ('a',), 'math', 1000, 300, True)]
    concepts, subjects = make_vocabs(history)
    model = LSTMErrorModel(len(concepts) + 1, len(subjects) + 1)
    predictor = LSTMPredictor(model, concepts, subjects)
    selector = ConceptSelector(
        InMemoryAttemptRepository(history), sequence_predictor=predictor
    )

    result = selector.select_next_concept(
        'learner', [CandidateConcept('a', 'math')], 2000
    )
    assert 0 <= result.predicted_error_probability <= 1

    unseen = selector.select_next_concept(
        'learner', [CandidateConcept('new', 'new subject')], 2000
    )
    assert 0 <= unseen.predicted_error_probability <= 1


def test_training_uses_prepared_batches():
    rows = [
        Interaction('learner', 'a1', 'q1', ('a',), 'math', 1000, 300, True),
        Interaction('learner', 'a2', 'q2', ('a',), 'math', 2000, 400, False),
    ]
    concepts, subjects = make_vocabs(rows)
    model = LSTMErrorModel(len(concepts) + 1, len(subjects) + 1)
    batch = collate_samples(make_samples(rows, concepts, subjects))

    losses = train_lstm(model, [batch], epochs=1)
    assert len(losses) == 1
    assert losses[0] >= 0
