"""Adaptive Study.

A project for UW-Madison's CS 539 _Intro to Artificial Neural Networks_ class.

This is a Neural Network-powered study assistant that tries to guess which facts
you're most likely to get wrong to help you learn them more effectively.
"""

import platformdirs
from sqlalchemy import create_engine

from ece539_adaptive_study_g17.database.database_controller import DatabaseController
from ece539_adaptive_study_g17.questions.question_controller import QuestionController
from ece539_adaptive_study_g17.ui.ui_app import UIApp

db_file = (
    platformdirs.user_data_path("Adaptive Study", "ECE/CS/MS 359 Group 17")
    / "adaptive_study_data.db"
)
engine = create_engine("sqlite:///" + str(db_file))


def main() -> None:
    """Run the program."""
    database_controller = DatabaseController(engine)
    question_controller = QuestionController(database_controller=database_controller)
    ui_app = UIApp(
        question_controller=question_controller, database_controller=database_controller
    )
    ui_app.run()


if __name__ == "__main__":
    main()
