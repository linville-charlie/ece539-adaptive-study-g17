"""Uses the trained model to select the next question."""

from database.concept import Concept, ConceptEvaluationData
from database.database_controller import DatabaseController


class ConceptSelector:
    """Uses the trained model to select the next question."""

    # TODO This should be a mock class until we can hook in the model.

    def __init__(self, database_controller: DatabaseController) -> None:
        """Create a question selector."""

    def select_concept(self, concept_eval_data: list[ConceptEvaluationData]) -> Concept:
        """Select a concept to build a question around."""
