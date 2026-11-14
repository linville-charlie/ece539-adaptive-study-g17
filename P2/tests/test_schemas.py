from dataclasses import replace
import pytest
from non_neural import Interaction


def record(**changes):
    base = Interaction('learner', 'i', 'q', ('a', 'b'), 'math', 100, None, True)
    return replace(base, **changes)


def test_valid_multiple_concepts():
    assert record().concept_ids == ('a', 'b')
    assert record(response_time_ms=0).response_time_ms == 0


@pytest.mark.parametrize('field', ['learner_id', 'interaction_id', 'question_id', 'subject_id'])
@pytest.mark.parametrize('value', ['', '  ', None, 1])
def test_missing_identifiers(field, value):
    with pytest.raises(ValueError, match=field):
        record(**{field: value})


@pytest.mark.parametrize('value', [-1, 1.5, True, None])
def test_invalid_timestamps(value):
    with pytest.raises(ValueError, match='timestamp_ms'):
        record(timestamp_ms=value)


@pytest.mark.parametrize('value', [-1, 1.5, True])
def test_invalid_response_times(value):
    with pytest.raises(ValueError, match='response_time_ms'):
        record(response_time_ms=value)


@pytest.mark.parametrize('value', [(), ('',), ('a', 'a'), 'a'])
def test_invalid_concepts(value):
    with pytest.raises(ValueError):
        record(concept_ids=value)


def test_correct_requires_boolean():
    with pytest.raises(ValueError, match='correct'):
        record(correct=1)


def test_list_concepts_are_copied_to_immutable_tuple():
    concepts = ['a', 'b']
    interaction = record(concept_ids=concepts)
    concepts.append('c')
    assert interaction.concept_ids == ('a', 'b')
