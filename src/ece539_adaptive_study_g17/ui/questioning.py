"""The main ask-answer-eval-repeat loop of the program."""

from tkinter import Frame

from ece539_adaptive_study_g17.questions.question_controller import QuestionController


class QuestioningUIComponent(Frame):
    """The main UI component for the ask-answer-eval-repeat loop of the program.

    Shows the user a question given by the `QuestionController` and the required
    interface to respond to that question. Once the user's answer has been input, it
    provides the answer to the `QuestionController` for processing, then displays the
    correct answer.
    """

    __question_controller: QuestionController

    def __init__(self, question_controller: QuestionController) -> None:
        """Create a Questioning UI Component."""
        super().__init__()
        raise NotImplementedError  # TODO
