"""Interface with the FLAN-T5 SLM to produce question text and evaluate the response."""

from ece539_adaptive_study_g17.questions.question import Question


class LanguageModelInterface:
    """The interface for the FLAN-T5 SLM."""

    def __init__(self) -> None:
        """Establish a FLAN-T5 interface."""
        raise NotImplementedError  # TODO

    def get_question_text(self, question: Question) -> str:
        """Get a question from the selected concept."""
        raise NotImplementedError  # TODO

    def generate_distractors(self, quesiton: Question) -> list[str]:
        """Generate distracts for multiple-choice & similar questions."""
        raise NotImplementedError  # TODO

    def evaluate_question_answer(self, question: Question, user_answer: str) -> bool:
        """Evaluate if a short-answer response is correct based on the question."""
        raise NotImplementedError  # TODO
