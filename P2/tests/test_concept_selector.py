"""Dependency-injection, isolation, and failure-policy tests."""
import pytest
from non_neural import (
    CandidateConcept, ConceptSelector, InMemoryAttemptRepository, Interaction,
    MockErrorPredictor, PredictionError,
)
from non_neural.adaptive_selector import SEVEN_DAYS_MS

NOW = SEVEN_DAYS_MS
A = CandidateConcept('a', 'math')
B = CandidateConcept('b', 'geography')


def attempt(i='1', learner='l', concept='a', time=0, correct=True):
    return Interaction(learner, i, 'q', [concept], 'math', time, None, correct)


def selector(attempts=(), probabilities=None, **kwargs):
    return ConceptSelector(
        InMemoryAttemptRepository(attempts),
        MockErrorPredictor(probabilities if probabilities is not None else {('math', 'a'): .9, ('geography', 'b'): .1}),
        **kwargs,
    )


def test_weighted_score_and_mixed_subject_metadata():
    result = selector([attempt()]).select_next_concept('l', [B, A], NOW)
    assert result.concept_id == 'a'
    assert result.subject_id == 'math'
    assert result.predicted_error_probability == .9
    assert result.recency_score == pytest.approx(.5)
    assert result.selection_score == pytest.approx(.82)
    assert not result.used_fallback


def test_alpha_and_recency_change_winner():
    history = [attempt(time=NOW)]
    assert selector(history, alpha=1).select_next_concept('l', [A, B], NOW + 1).concept_id == 'a'
    result = selector(history, alpha=0).select_next_concept('l', [A, B], NOW + 1)
    assert result.concept_id == 'b'
    assert result.recency_score == 1


def test_learner_isolation_single_history_fetch_and_predictor_inputs():
    class Repository(InMemoryAttemptRepository):
        calls = 0

        def get_history(self, learner_id, before_timestamp_ms=None):
            self.calls += 1
            return super().get_history(learner_id, before_timestamp_ms)

    class Predictor:
        calls = []

        def predict_error(self, learner_id, concept_id, subject_id, features):
            self.calls.append((learner_id, concept_id, subject_id, features))
            return .4

    repo = Repository([attempt(correct=False), attempt('2', learner='other'), attempt('3', time=NOW)])
    predictor = Predictor()
    result = ConceptSelector(repo, predictor).select_next_concept('l', [B, A], NOW)
    assert repo.calls == 1
    assert [(c[1], c[2]) for c in predictor.calls] == [('a', 'math'), ('b', 'geography')]
    assert predictor.calls[0][3]['skill_accuracy'] == 0
    assert predictor.calls[0][3]['overall_attempt_count'] == 1
    assert predictor.calls[1][3]['skill_accuracy'] is None
    assert result.concept_id == 'b'


def test_cold_start_and_deterministic_tie():
    s = selector(probabilities={('math', 'a'): .5, ('geography', 'b'): .5})
    first = s.select_next_concept('l', [B, A], 0)
    assert first == s.select_next_concept('l', [A, B], 0)
    assert first.concept_id == 'a'
    assert first.recency_score == 1
    assert first.selection_score == pytest.approx(.6)


@pytest.mark.parametrize('concepts', [[], [A, A], [A, CandidateConcept('a', 'other')], ['a']])
def test_invalid_candidates(concepts):
    with pytest.raises(ValueError):
        selector().select_next_concept('l', concepts, NOW)


@pytest.mark.parametrize('value', [-1, 1.1, float('nan'), float('inf'), True, None, '0.5'])
def test_invalid_probabilities_are_not_hidden_by_fallback(value):
    with pytest.raises(ValueError, match='probability'):
        selector(probabilities={('math', 'a'): value}, fallback_error_probability=.5).select_next_concept('l', [A], NOW)


class BrokenPredictor:
    def predict_error(self, *args):
        raise RuntimeError('offline')


def test_predictor_exception_is_chained_by_default():
    class Broken:
        def predict_error(self, *args):
            raise RuntimeError('offline')
    s = ConceptSelector(InMemoryAttemptRepository(), Broken())
    with pytest.raises(PredictionError, match='a') as error:
        s.select_next_concept('l', [A], NOW)
    assert isinstance(error.value.__cause__, RuntimeError)


def test_explicit_fallback_is_reported():
    s = ConceptSelector(InMemoryAttemptRepository(), BrokenPredictor(), fallback_error_probability=.25)
    result = s.select_next_concept('l', [A], NOW)
    assert result.used_fallback
    assert result.predicted_error_probability == .25
    assert result.selection_score == pytest.approx(.4)


@pytest.mark.parametrize('kwargs', [{'alpha': 2}, {'half_life_ms': 0}, {'fallback_error_probability': -.1}])
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        selector(**kwargs)


def test_repository_failures_propagate():
    class BrokenRepository:
        def get_history(self, *args):
            raise RuntimeError('database unavailable')
    s = ConceptSelector(BrokenRepository(), MockErrorPredictor({}), fallback_error_probability=.5)
    with pytest.raises(RuntimeError, match='database unavailable'):
        s.select_next_concept('l', [A], NOW)


def test_repository_wrong_learner_is_rejected():
    class WrongRepository:
        def get_history(self, *args):
            return [attempt(learner='other')]
    with pytest.raises(ValueError, match='different learner'):
        ConceptSelector(WrongRepository(), MockErrorPredictor({})).select_next_concept('l', [A], NOW)


def test_custom_half_life():
    result = selector([attempt()], half_life_ms=NOW * 2).select_next_concept('l', [A], NOW)
    assert result.recency_score == pytest.approx(1 - 2 ** -.5)


def test_rank_all_candidates_once_with_components():
    class Predictor:
        calls = []

        def predict_error(self, learner_id, concept_id, subject_id, features):
            self.calls.append(concept_id)
            return {'a': .9, 'b': .1}[concept_id]

    predictor = Predictor()
    service = ConceptSelector(InMemoryAttemptRepository([attempt()]), predictor)
    results = service.rank_concepts('l', [B, A], NOW)
    assert [r.concept_id for r in results] == ['a', 'b']
    assert predictor.calls == ['a', 'b']
    assert results[0].selection_score == pytest.approx(.82)
    assert results[1].selection_score == pytest.approx(.28)
    assert all(0 <= r.selection_score <= 1 for r in results)


def test_sequence_predictor_receives_only_past_history_and_read_only_features():
    from dataclasses import replace
    from non_neural import FEATURE_NAMES

    past = attempt('past', time=0, correct=False)
    tied = replace(attempt('tied', time=0), question_id='q-again')
    target = attempt('target', time=NOW)
    future = attempt('future', time=NOW + 1)

    class UnfilteredRepository:
        def get_history(self, *args):
            return [future, past, target, tied]

    class SequencePredictor:
        requests = []

        def predict_error(self, request):
            self.requests.append(request)
            assert request.history == (past, tied)
            assert request.prediction_timestamp_ms == NOW
            assert request.learner_id == 'l'
            assert request.features['overall_attempt_count'] == 2
            assert request.features['previous_correct'] == 1
            assert request.features['skill_accuracy'] == .5
            with pytest.raises(TypeError):
                request.features['skill_accuracy'] = 1
            duration_index = FEATURE_NAMES.index('skill_avg_response_time')
            assert not request.feature_vector.observed_mask[duration_index]
            return .75

    model = SequencePredictor()
    result = ConceptSelector(UnfilteredRepository(), sequence_predictor=model).select_next_concept('l', [A], NOW)
    assert result.predicted_error_probability == .75
    assert model.requests[0].subject_id == 'math'


def test_legacy_predictor_mutation_cannot_change_recency():
    class MutatingPredictor:
        def predict_error(self, learner_id, concept_id, subject_id, features):
            features['time_since_last_skill_attempt'] = None
            return .5

    result = ConceptSelector(InMemoryAttemptRepository([attempt()]), MutatingPredictor()).select_next_concept('l', [A], NOW)
    assert result.recency_score == pytest.approx(.5)
    assert result.selection_score == pytest.approx(.5)


def test_sequence_failures_follow_the_same_policy():
    class BrokenSequencePredictor:
        def predict_error(self, request):
            raise OSError('model unavailable')

    repository = InMemoryAttemptRepository()
    model = BrokenSequencePredictor()
    with pytest.raises(PredictionError) as error:
        ConceptSelector(repository, sequence_predictor=model).select_next_concept('l', [A], NOW)
    assert isinstance(error.value.__cause__, OSError)
    result = ConceptSelector(repository, sequence_predictor=model, fallback_error_probability=.5).select_next_concept('l', [A], NOW)
    assert result.used_fallback
    assert result.selection_score == pytest.approx(.6)


def test_sequence_invalid_probabilities_do_not_fallback():
    class InvalidSequencePredictor:
        def predict_error(self, request):
            return float('nan')

    with pytest.raises(ValueError, match='probability'):
        ConceptSelector(InMemoryAttemptRepository(), sequence_predictor=InvalidSequencePredictor(), fallback_error_probability=.5).select_next_concept('l', [A], NOW)


def test_exactly_one_predictor_api_is_required():
    repository = InMemoryAttemptRepository()
    with pytest.raises(ValueError, match='exactly one'):
        ConceptSelector(repository)
    with pytest.raises(ValueError, match='exactly one'):
        ConceptSelector(repository, MockErrorPredictor({}), sequence_predictor=MockErrorPredictor({}))


@pytest.mark.parametrize('history', [[{}], [attempt(), attempt()]])
def test_malformed_repository_history_rejected_before_predicting(history):
    class Repository:
        def get_history(self, *args):
            return history

    with pytest.raises(ValueError):
        ConceptSelector(Repository(), MockErrorPredictor({})).select_next_concept('l', [A], NOW)
