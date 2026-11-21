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
"""A user's answer to a question."""

from typing import Protocol

from ece539_adaptive_study_g17.questions.question import (
    MultipleChoiceQuestion,
    Question,
    ShortAnswerQuestion,
)


class Answer(Protocol):
    """A user's answer to a question."""

    def question(self) -> Question:
        """Get the question this answer is for."""
        ...

    def payload(self) -> str:
        """Get a consistent representation of an answer."""
        ...


class MultipleChoiceAnswer(Answer):
    """The answer to a multiple choice question."""

    # TODO determine if multiple-choice should have UI buttons or have the same
    # text-based interface as short answer, just with n options provided.
    # Right now, it's spec'd out to be its own UI component.
    def __init__(self, question: MultipleChoiceQuestion, answer: int) -> None:
        """Create a new multiple choice answer."""
        raise NotImplementedError  # TODO

    # TODO Implement protocol methods.


class ShortAnswerAnswer(Answer):
    """The answer to a multiple choice question."""

    def __init__(self, question: ShortAnswerQuestion, answer: int) -> None:
        """Create a new multiple choice answer."""
        raise NotImplementedError  # TODO

    # TODO Implement protocol methods.
