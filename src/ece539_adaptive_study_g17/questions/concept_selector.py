"""Uses the trained model to select the next question."""

from ece539_adaptive_study_g17.database.concept import Concept, ConceptEvaluationData


class ConceptSelector:
    """Uses the trained model to select the next question."""

    # TODO This should be a mock class until we can hook in the model.

    def __init__(self) -> None:
        """Create a question selector."""
        raise NotImplementedError  # TODO

    def select_concept(self, concept_eval_data: list[ConceptEvaluationData]) -> Concept:
        """Select a concept to build a question around."""
        raise NotImplementedError  # TODO
