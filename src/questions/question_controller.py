"""Management of the questioning system."""

from database.database_controller import DatabaseController
from questions.question import Question


class QuestionController:
    """Manages the questioning system."""

    def __init__(self, database_controller: DatabaseController) -> None:
        """Create a question controller."""

    def select_next_question(self) -> Question:
        """Select the next question the user should see."""

    def accept_quesiton_answer(self, question: Question, answer) -> None:
        """Accept the answer to a quesiton and update data correspondingly."""
