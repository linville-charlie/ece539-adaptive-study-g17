"""Main access point for the UI and driver of the program."""

from questions.question_controller import QuestionController


class UIApp:
    """The base UI application that manages the display of other UI components."""

    def __init__(self, question_controler: QuestionController) -> None:
        """Create the UI manager."""

    def run() -> None:
        """Execute the application."""
