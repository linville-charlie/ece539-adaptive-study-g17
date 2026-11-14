import math
import pytest
from non_neural import FEATURE_NAMES, Interaction, extract_features


def row(i, correct=True, concepts=('a',), duration=100, learner='l'):
    return Interaction(learner, str(i), 'q', concepts, 's', i * 1000, duration, correct)


def test_empty():
    f = extract_features([], 'a', 0)
    assert list(f) == FEATURE_NAMES
    assert f['skill_attempt_count'] == f['overall_attempt_count'] == f['skill_correct_streak'] == 0
    assert all(v is None for k, v in f.items() if k not in {
        'skill_attempt_count', 'overall_attempt_count', 'skill_correct_streak'})


def test_single():
    assert extract_features([row(1)], 'a', 1500) == dict(zip(FEATURE_NAMES, [
        100, 1, 500, 500, 1, 100, 1, 100, 1, 1, 1, 1]))


def test_concept_and_overall_statistics():
    history = [row(1, False, duration=200), row(2, concepts=('b',)),
               row(3, concepts=('a', 'b'), duration=400), row(4, duration=None)]
    f = extract_features(history, 'a', 5000)
    assert f['skill_accuracy'] == pytest.approx(2 / 3)
    assert f['overall_accuracy'] == .75
    assert f['skill_attempt_count'] == 3
    assert f['overall_attempt_count'] == 4
    assert f['skill_avg_response_time'] == 300
    assert f['skill_correct_streak'] == 2
    assert f['previous_response_time'] is None
    assert extract_features(history, 'b', 5000)['time_since_last_skill_attempt'] == 2000


def test_recent_window_uses_natural_log_and_skill_attempts():
    history = [row(i, i > 50, duration=i) for i in range(1, 101)]
    f = extract_features(history, 'a', 101000)
    count = min(100, 50, math.floor(10 * math.log(101)))
    assert count == 46
    assert f['recent_skill_accuracy'] == 1
    assert f['recent_skill_avg_response_time'] == (55 + 100) / 2
    assert f['skill_accuracy'] == .5
    assert f['skill_correct_streak'] == 50
    assert extract_features([row(i) for i in range(1, 301)], 'a', 301000)['recent_skill_avg_response_time'] == 100


def test_missing_durations_and_unseen_concept():
    f = extract_features([row(1, duration=None)], 'a', 2000)
    assert f['skill_avg_response_time'] is f['recent_skill_avg_response_time'] is None
    unseen = extract_features([row(1)], 'new', 2000)
    assert unseen['skill_accuracy'] is unseen['time_since_last_skill_attempt'] is None
    assert unseen['skill_attempt_count'] == unseen['skill_correct_streak'] == 0
    assert unseen['overall_accuracy'] == 1


def test_no_current_or_future_answer_leakage():
    past = [row(1, False)]
    assert extract_features(past + [row(2), row(3)], 'a', 2000) == extract_features(past, 'a', 2000)
    assert extract_features([row(2)], 'a', 2000)['overall_attempt_count'] == 0


def test_streak_resets_and_ignores_other_concepts():
    assert extract_features([row(1), row(2, False)], 'a', 3000)['skill_correct_streak'] == 0
    assert extract_features([row(1), row(2, False, ('b',))], 'a', 3000)['skill_correct_streak'] == 1


@pytest.mark.parametrize('history', [[row(1), row(1)], [row(1), row(2, learner='other')]])
def test_invalid_histories(history):
    with pytest.raises(ValueError):
        extract_features(history, 'a', 3000)


def test_recent_window_caps_at_fifty():
    history = [row(i, i > 250, duration=i) for i in range(1, 301)]
    f = extract_features(history, 'a', 301000)
    assert f['recent_skill_accuracy'] == 1
    assert f['recent_skill_avg_response_time'] == (251 + 300) / 2


def test_recent_window_retains_missing_duration_attempts():
    history = [row(i, duration=i if i <= 54 else None) for i in range(1, 101)]
    f = extract_features(history, 'a', 101000)
    assert f['recent_skill_avg_response_time'] is None
    assert f['recent_skill_accuracy'] == 1
    assert f['skill_avg_response_time'] == 27.5


def test_unsorted_history_is_sorted_without_mutation():
    history = [row(3), row(1), row(2, False)]
    original = list(history)
    assert extract_features(history, 'a', 4000) == extract_features(sorted(history, key=lambda r: r.timestamp_ms), 'a', 4000)
    assert history == original


def test_equal_timestamp_order_is_stable_and_target_time_excluded():
    from dataclasses import replace
    a = row(1, False)
    b = replace(row(2), timestamp_ms=1000)
    f = extract_features([a, b], 'a', 2000)
    assert f['previous_correct'] == 1
    assert f['skill_correct_streak'] == 1
    assert extract_features([b, a], 'a', 2000)['skill_correct_streak'] == 0
    assert extract_features([a, b], 'a', 1000)['overall_attempt_count'] == 0


def test_recent_threshold_147_and_148():
    for n, expected in [(147, 49), (148, 50)]:
        history = [row(i, duration=i) for i in range(1, n + 1)]
        f = extract_features(history, 'a', (n + 1) * 1000)
        assert f['recent_skill_avg_response_time'] == (n - expected + 1 + n) / 2


def test_vector_mask_distinguishes_zero_from_unknown():
    from non_neural import to_feature_vector
    features = extract_features([], 'a', 0)
    vector = to_feature_vector(dict(reversed(list(features.items()))))
    assert len(vector.values) == len(vector.observed_mask) == 12
    for i, name in enumerate(FEATURE_NAMES):
        assert vector.observed_mask[i] == (features[name] is not None)
        assert vector.values[i] == (0.0 if features[name] is None else features[name])
    assert not vector.observed_mask[FEATURE_NAMES.index('skill_accuracy')]
    assert vector.observed_mask[FEATURE_NAMES.index('skill_attempt_count')]


@pytest.mark.parametrize('change', [{'extra': 0}, {'skill_accuracy': float('nan')}, {'skill_accuracy': True}, {'skill_accuracy': '0'}])
def test_invalid_vector(change):
    from non_neural import to_feature_vector
    features = extract_features([], 'a', 0)
    features.update(change)
    with pytest.raises(ValueError):
        to_feature_vector(features)


def test_vector_rejects_missing_key():
    from non_neural import to_feature_vector
    with pytest.raises(ValueError):
        to_feature_vector({})


def test_repeated_question_is_multiple_distinct_attempts():
    from dataclasses import replace
    first = row(1, False, duration=200)
    second = replace(row(2, duration=400), question_id=first.question_id)
    f = extract_features([second, first], 'a', 3000)
    assert f['skill_attempt_count'] == f['overall_attempt_count'] == 2
    assert f['skill_accuracy'] == .5
    assert f['skill_avg_response_time'] == 300
