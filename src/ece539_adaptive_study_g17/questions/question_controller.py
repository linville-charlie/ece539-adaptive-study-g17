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
#
# This file header was last modified 21 Nov 2026.
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
