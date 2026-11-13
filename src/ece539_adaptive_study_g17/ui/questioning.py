"""The main ask-answer-eval-repeat loop of the program."""

from tkinter import Tk, Widget

from questions.question_controller import QuestionController


class QuestioningUIComponent(Widget):
    """The main UI component for the ask-answer-eval-repeat loop of the program.

    Shows the user a question given by the `QuestionController` and the required
    interface to respond to that question. Once the user's answer has been input, it
    provides the answer to the `QuestionController` for processing, then displays the
    correct answer.
    """

    __question_controller: QuestionController

    def __init__(
        self, parent: Widget | Tk, name: str, question_controller: QuestionController
    ) -> None:
        """Create a Questioning UI Component."""
        super().__init__(master=parent, widgetName=name)
