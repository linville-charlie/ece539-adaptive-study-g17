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
"""Questions to ask the user and their types."""

from ece539_adaptive_study_g17.database.concept import Concept
from ece539_adaptive_study_g17.database.fact import Fact


class Question:
    """A question to ask the user."""

    def __init__(
        self,
        concept: Concept,
        context_facts: list[Fact],
        answer_fact: Fact,
        type: QuestionType,
    ) -> None:
        """Create a question."""
        raise NotImplementedError  # TODO


class QuestionType:
    """A type of question."""


class MultipleChoiceQuestion(QuestionType):
    """A multiple choice question."""

    number_responses: int = 4

    def __init__(self) -> None:
        """Specify a multiple choice question."""
        raise NotImplementedError  # TODO


class ShortAnswerQuestion(QuestionType):
    """A short answer question."""

    def __init__(self) -> None:
        """Specify a multiple choice question."""
        raise NotImplementedError  # TODO
