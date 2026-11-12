"""Interface with the FLAN-T5 SLM to produce question text and evaluate the response."""

from questions.question import Question


class FLANInterface:
    """The interface for the FLAN-T5 SLM."""

    def __init__(self) -> None:
        """Establish a FLAN-T5 interface."""

    def get_question_text(self, question: Question) -> str:
        """Get a quesiton from the selected concept."""

    def generate_distractors(self, quesiton: Question) -> str:
        """Generate distractors for multiple-choice & similar questions."""

    def evaluate_quesiton_answer(self, question: Question, user_answer: str) -> bool:
        """Evaluate if a short-answer response is correct based on the question."""
