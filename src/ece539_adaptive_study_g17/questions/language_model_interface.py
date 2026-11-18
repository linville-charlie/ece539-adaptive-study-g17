"""Interface with the FLAN-T5 SLM to produce question text and evaluate the response."""

from dataclasses import dataclass

from ece539_adaptive_study_g17.database.fact import Fact
from ece539_adaptive_study_g17.questions.answer import Answer
from ece539_adaptive_study_g17.questions.question import Question


class LanguageModelInterface:
    """The interface for the FLAN-T5 SLM."""

    def __init__(self) -> None:
        """Establish a FLAN-T5 interface."""
        raise NotImplementedError  # TODO

    def get_question_text(self, question: Question) -> str:
        """Get a question from the selected concept."""
        raise NotImplementedError  # TODO

    def generate_distractors(
        self, question: Question, similar_facts: list[Fact]
    ) -> list[str]:
        """Generate distracts for multiple-choice & similar questions."""
        raise NotImplementedError  # TODO

    def evaluate_question_answer(self, answer: Answer) -> AnswerResult:
        """Evaluate if a the user's response is correct."""
        raise NotImplementedError  # TODO


@dataclass(frozen=True, slots=True)
class AnswerResult:
    """Language Model answer evaluation result."""

    is_correct: bool
    correct_answer: str  # to show the user
    explanation: str | None = None
