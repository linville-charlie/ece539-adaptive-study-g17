import pytest
from non_neural import select_concept
from non_neural.adaptive_selector import SEVEN_DAYS_MS


def test_highest_priority():
    result = select_concept({'a': .9, 'b': .2}, {'a': 0, 'b': 0}, 0)
    assert result.concept_id == 'a'
    assert result.score == pytest.approx(.72)


def test_recency_half_life_and_never_reviewed():
    now = 2 * SEVEN_DAYS_MS
    for reviewed, expected in [(now, 0), (SEVEN_DAYS_MS, .5), (0, .75), (None, 1)]:
        result = select_concept({'a': .2}, {'a': reviewed}, now, alpha=0)
        assert result.score == pytest.approx(expected)
    assert select_concept({'a': .2}, {}, now, alpha=0).score == 1


def test_alpha_changes_selection():
    probabilities = {'a': .9, 'b': .1}
    reviews = {'a': 100, 'b': None}
    assert select_concept(probabilities, reviews, 100, alpha=1).concept_id == 'a'
    assert select_concept(probabilities, reviews, 100, alpha=0).concept_id == 'b'


def test_tie_breaking_ignores_mapping_order():
    assert select_concept({'b': .5, 'a': .5}, {}, 0).concept_id == 'a'


def test_empty():
    with pytest.raises(ValueError, match='candidate'):
        select_concept({}, {}, 0)


@pytest.mark.parametrize('value', [-.1, 1.1, float('nan'), float('inf'), True, '0.5'])
def test_invalid_probability(value):
    with pytest.raises(ValueError, match='probability'):
        select_concept({'a': value}, {}, 0)


@pytest.mark.parametrize('kwargs', [{'alpha': -1}, {'alpha': float('nan')}, {'half_life_ms': 0}, {'half_life_ms': -1}, {'half_life_ms': float('inf')}])
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        select_concept({'a': .5}, {}, 0, **kwargs)


def test_future_review():
    with pytest.raises(ValueError, match='future'):
        select_concept({'a': .5}, {'a': 1}, 0)
