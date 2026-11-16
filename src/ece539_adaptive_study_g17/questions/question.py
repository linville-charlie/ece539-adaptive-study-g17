"""Questions to ask the user and their types."""

from ece539_adaptive_study_g17.database.concept import Concept
from ece539_adaptive_study_g17.database.fact import Fact


class Question:
    """A question to ask the user."""

    def __init__(
        self,
        concept: Concept,
        context_facts: list[Fact],
        answer_fact: Fact,
        type: QuestionType,
    ) -> None:
        """Create a question."""
        raise NotImplementedError  # TODO


class QuestionType:
    """A type of question."""


class MultipleChoiceQuestion(QuestionType):
    """A multiple choice question."""

    number_responses: int = 4

    def __init__(self) -> None:
        """Specify a multiple choice question."""
        raise NotImplementedError  # TODO
