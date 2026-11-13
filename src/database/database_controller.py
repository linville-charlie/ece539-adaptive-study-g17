"""Interact with the local sqlite databse using `sqlalchemy`."""

from database.concept import Concept, ConceptEvaluationData


class DatabaseController:
    """Interact with the local sqlite databse using `sqlalchemy`."""

    def get_concept_by_id(self) -> Concept:
        """Return a Concept to for question generation and answer evaluation."""

    def get_concepts_for_selection(self) -> list[ConceptEvaluationData]:
        """Return data on all concepts for concept selection."""
