"""Management of the questioning system."""

from ece539_adaptive_study_g17.database.database_controller import DatabaseController
from ece539_adaptive_study_g17.questions.answer import Answer
from ece539_adaptive_study_g17.questions.language_model_interface import AnswerResult
from ece539_adaptive_study_g17.questions.question import Question


class QuestionController:
    """Manages the questioning system."""

    def __init__(self, database_controller: DatabaseController) -> None:
        """Create a question controller."""
        raise NotImplementedError  # TODO

    def select_next_question(self) -> Question:
        """Select the next question the user should see."""
        raise NotImplementedError  # TODO

    def accept_question_answer(self, answer: Answer) -> AnswerResult:
        """Accept the answer to a question and update data correspondingly."""
        raise NotImplementedError  # TODO
