#   539g17 Adaptive Study Integration Project
#   Copyright (C) 2026  A. Kancherla, C. Linville, Q. Schultz, E. Wulf.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Authors of this file:
#
# - Quentin Schultz
# - Aniketh Kancherla
#
# This file header was last modified 27 Nov 2026.
"""Adaptive Study.

A project for UW-Madison's CS 539 _Intro to Artificial Neural Networks_ class.

This is a Neural Network-powered study assistant that tries to guess which facts
you're most likely to get wrong to help you learn them more effectively.
"""


def main() -> None:
    """Run the program."""
    # ruff: noqa: PLC0415 -- Keep offline dataset commands independent of the GUI.
    # Import the desktop application only when launching it. Dataset tools are headless.
    import platformdirs
    from sqlalchemy import create_engine

    from ece539_adaptive_study_g17.database.database_controller import (
        DatabaseController,
    )
    from ece539_adaptive_study_g17.questions.question_controller import (
        QuestionController,
    )
    from ece539_adaptive_study_g17.ui.ui_app import UIApp

    db_file = (
        platformdirs.user_data_path("Adaptive Study", "ECE/CS/MS 359 Group 17")
        / "adaptive_study_data.db"
    )
    if not db_file.exists():
        db_file.parent.mkdir(parents=True)

    engine = create_engine("sqlite:///" + str(db_file))

    database_controller = DatabaseController(engine)
    question_controller = QuestionController(database_controller=database_controller)
    ui_app = UIApp(
        question_controller=question_controller, database_controller=database_controller
    )
    ui_app.run()


if __name__ == "__main__":
    main()
