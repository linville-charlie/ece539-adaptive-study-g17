"""Interact with the local sqlite database using `sqlalchemy`."""
from sqlalchemy import Engine

from ece539_adaptive_study_g17.database.concept import Concept, ConceptEvaluationData


class DatabaseController:
    """Interact with the local sqlite database using `sqlalchemy`."""

    def __init__(self, engine: Engine) -> None:
        """Create the database controller."""
        raise NotImplementedError  # TODO

    def get_concept_by_id(self, id: int) -> Concept:
        """Return a Concept to for question generation and answer evaluation."""
        raise NotImplementedError  # TODO

    def get_concepts_for_selection(self) -> list[ConceptEvaluationData]:
        """Return data on all concepts for concept selection."""
        raise NotImplementedError  # TODO
