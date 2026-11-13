"""Questions to ask the user and their types."""

from abc import ABC

from database.concept import Concept
from database.fact import Fact


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


class QuestionType(ABC):
    """A type of quesiton."""


class MultipleChoiceQuestion(QuestionType):
    """A multiple choice question."""

    number_responses: int = 4

    def __init__(self) -> None:
        """Specify a multiple choice question."""
        super().__init__()
