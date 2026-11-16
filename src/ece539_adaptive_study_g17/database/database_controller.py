"""Interact with the local sqlite databse using `sqlalchemy`."""

from ece539_adaptive_study_g17.database.concept import Concept, ConceptEvaluationData


class DatabaseController:
    """Interact with the local sqlite databse using `sqlalchemy`."""

    def get_concept_by_id(self) -> Concept:
        """Return a Concept to for question generation and answer evaluation."""
        raise NotImplementedError  # TODO

    def get_concepts_for_selection(self) -> list[ConceptEvaluationData]:
        """Return data on all concepts for concept selection."""
        raise NotImplementedError  # TODO
