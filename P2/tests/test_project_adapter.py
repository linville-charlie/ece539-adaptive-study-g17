"""Exercise the PR-compatible facade with fake project objects, not the ORM."""
from dataclasses import dataclass
import pytest
from non_neural import (
    CandidateConcept, ConceptSelector, ControllerConceptSelector,
    DatabaseAttemptRepository, InMemoryAttemptRepository, Interaction, MockErrorPredictor,
)


@dataclass
class ProjectConcept:
    id: int
    subject: str


def test_controller_facade_returns_original_project_concept():
    concepts = [ProjectConcept(10, 'math'), ProjectConcept(20, 'geography')]
    lookups = {str(c.id): c for c in concepts}
    clock_calls = []

    def clock():
        clock_calls.append(1)
        return 1000

    core = ConceptSelector(InMemoryAttemptRepository(), MockErrorPredictor({('math', '10'): .9, ('geography', '20'): .2}))
    facade = ControllerConceptSelector(
        core, learner_id='local-user',
        to_candidate=lambda item: CandidateConcept(str(item.id), item.subject),
        get_concept_by_id=lookups.__getitem__, prediction_clock_ms=clock,
    )
    assert facade.select_concept(concepts) is concepts[0]
    assert facade.last_selection.concept_id == '10'
    assert facade.last_selection.selection_score == pytest.approx(.92)
    assert clock_calls == [1]
    with pytest.raises(ValueError):
        facade.select_concept([])
    assert facade.last_selection is None


def test_database_method_name_bridge_delegates_cutoff_and_learner():
    interaction = Interaction('local-user', 'i1', 'q', ['a'], 'math', 1, None, True)

    class Controller:
        queries = []

        def get_attempt_history(self, learner_id, before_timestamp_ms=None):
            self.queries.append((learner_id, before_timestamp_ms))
            return [interaction]

    controller = Controller()
    repository = DatabaseAttemptRepository(controller)
    assert repository.get_history('local-user', 1000) == [interaction]
    assert controller.queries == [('local-user', 1000)]
    repository.get_history('local-user')
    assert controller.queries[-1] == ('local-user', None)
    with pytest.raises(ValueError):
        repository.get_history('', 1000)
    with pytest.raises(ValueError):
        repository.get_history('local-user', -1)


def test_lookup_errors_are_not_hidden():
    def failed_lookup(concept_id):
        raise KeyError(concept_id)

    facade = ControllerConceptSelector(
        ConceptSelector(InMemoryAttemptRepository(), MockErrorPredictor({('math', 'a'): .5})),
        learner_id='l', to_candidate=lambda item: item,
        get_concept_by_id=failed_lookup, prediction_clock_ms=lambda: 1000,
    )
    with pytest.raises(KeyError):
        facade.select_concept([CandidateConcept('a', 'math')])
    assert facade.last_selection is None


def test_database_source_errors_propagate():
    class Controller:
        def get_attempt_history(self, *args):
            raise OSError('database locked')

    with pytest.raises(OSError, match='database locked'):
        DatabaseAttemptRepository(Controller()).get_history('l', 1000)
