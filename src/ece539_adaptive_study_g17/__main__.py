"""Execute the study app implemented in this module."""

from sqlalchemy import create_engine

from ece539_adaptive_study_g17.database.database_controller import DatabaseController
from ece539_adaptive_study_g17.questions.question_controller import QuestionController
from ece539_adaptive_study_g17.ui.ui_app import UIApp


def main() -> None:
    """Run the program."""
    engine = create_engine("sqlite:///myfile.db", connect_args={"autocommit": False})
    database_controller = DatabaseController(engine)
    question_controller = QuestionController(database_controller=database_controller)
    ui_app = UIApp(
        question_controller=question_controller, database_controller=database_controller
    )
    ui_app.run()


if __name__ == "__main__":
    main()
