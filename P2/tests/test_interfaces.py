"""In-memory adapter behavior required of the future SQLite repository."""
import pytest
from non_neural import InMemoryAttemptRepository, Interaction, MockErrorPredictor


def row(i, time, learner='l'):
    return Interaction(learner, i, 'q', ['a', 'b'], 'math', time, None, True)


def test_repository_filters_sorts_and_preserves_ties():
    a, b, c = row('a', 1), row('b', 1), row('c', 2)
    repository = InMemoryAttemptRepository([c, a, row('other', 0, 'other'), b])
    assert repository.get_history('l') == [a, b, c]
    assert repository.get_history('l', 2) == [a, b]
    assert repository.get_history('l', 1) == []
    assert repository.get_history('unknown') == []
    copy = repository.get_history('l')
    copy.clear()
    assert len(repository.get_history('l')) == 3


def test_repository_add_and_duplicate_rejection():
    repository = InMemoryAttemptRepository()
    repository.add(row('a', 1))
    with pytest.raises(ValueError, match='duplicate'):
        repository.add(row('a', 2, 'other'))
    with pytest.raises(ValueError, match='Interaction'):
        repository.add({})


@pytest.mark.parametrize('learner, cutoff', [('', None), ('l', -1), ('l', True)])
def test_invalid_query(learner, cutoff):
    with pytest.raises(ValueError):
        InMemoryAttemptRepository().get_history(learner, cutoff)


def test_mock_is_subject_specific_and_missing_key_raises():
    predictor = MockErrorPredictor({('math', 'a'): .2, ('geography', 'a'): .7})
    assert predictor.predict_error('l', 'a', 'math', {}) == .2
    assert predictor.predict_error('l', 'a', 'geography', {}) == .7
    with pytest.raises(KeyError):
        predictor.predict_error('l', 'new', 'math', {})
