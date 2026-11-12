"""Adaptive Study.

A project for UW-Madison's CS 539 _Intro to Artificial Neural Networks_ class.

This is a Neural Network-powered study assistant that tries to guess which facts
you're most likely to get wrong to help you learn them more effectively.
"""

from database.database_controller import DatabaseController
from ece539_adaptive_study_g17.ui.ui_app import UIApp
from questions.question_controller import QuestionController


def main() -> None:
    """Run the program."""
    database_controller = DatabaseController()
    question_controller = QuestionController(database_controller=database_controller)
    ui_app = UIApp(
        question_controler=question_controller, database_controller=database_controller
    )
    ui_app.run()


if __name__ == "__main__":
    main()
