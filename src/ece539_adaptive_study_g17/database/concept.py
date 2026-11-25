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
# - Ella Wulf
#
# This file header was last modified 25 Nov 2026.
"""Manages database and project concepts."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ece539_adaptive_study_g17.database import CONCEPT_TABLE, FIELD_TABLE_ID
from ece539_adaptive_study_g17.database.base_table import _BaseDatabaseTable
from ece539_adaptive_study_g17.database.fact import Fact

if TYPE_CHECKING:
    from ece539_adaptive_study_g17.database.attempt import Attempt
    from ece539_adaptive_study_g17.database.field import Field


class Concept(_BaseDatabaseTable):
    """Represents a group of related information."""

    __tablename__ = CONCEPT_TABLE

    id: Mapped[int] = mapped_column(primary_key=True)

    field_id: Mapped[int] = mapped_column(
        ForeignKey(FIELD_TABLE_ID, ondelete="RESTRICT"), index=True
    )
    field: Mapped[Field] = relationship()

    facts: Mapped[list[Fact]] = relationship(back_populates="concept")

    attempts: Mapped[list[Attempt]] = relationship(
        back_populates="concept",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Attempt.timestamp_ms",
    )

    def get_evaluation_data(self) -> ConceptEvaluationData:
        """Get the historic data for use in selection.

        A concept with no attempts gets zeros everywhere.
        """
        # Oldest first. The relationship is already ordered when loaded from the
        # database; sorting again also covers attempts added in this session.
        attempts = sorted(self.attempts, key=lambda attempt: attempt.timestamp_ms)
        recent = attempts[len(attempts) - recent_window_size(len(attempts)) :]

        # Count correct answers in a row, walking back from the newest attempt.
        streak = 0
        for attempt in reversed(attempts):
            if not attempt.was_correct:
                break
            streak += 1

        return ConceptEvaluationData(
            concept_id=self.id,
            attempt_count=len(attempts),
            avg_response_time_ms=_average_response_time_ms(attempts),
            accuracy=_accuracy(attempts),
            recent_avg_response_time_ms=_average_response_time_ms(recent),
            recent_accuracy=_accuracy(recent),
            correct_streak=streak,
        )


RECENT_ATTEMPT_CAP = 50
"""The most attempts that ever count as 'recent'."""


def recent_window_size(attempt_count: int) -> int:
    """Return how many of the newest attempts count as 'recent'.

    Per the README: floor(10 * log10(attempt_count + 1)), at most 50, and never
    more than the attempts that exist.
    """
    window = math.floor(10 * math.log10(attempt_count + 1))
    return min(window, RECENT_ATTEMPT_CAP, attempt_count)


def _accuracy(attempts: Sequence[Attempt]) -> float:
    """Fraction of attempts answered correctly; 0.0 when there are none."""
    if not attempts:
        return 0.0
    return sum(attempt.was_correct for attempt in attempts) / len(attempts)


def _average_response_time_ms(attempts: Sequence[Attempt]) -> int:
    """Mean response time, rounded to whole ms; 0 when there are none."""
    if not attempts:
        return 0
    return round(sum(attempt.response_time_ms for attempt in attempts) / len(attempts))


@dataclass(frozen=True, slots=True)
class ConceptEvaluationData:
    """The data stored in a concept that the selector uses to evaluate it."""

    # TODO Confirm training data
    concept_id: int
    attempt_count: int
    avg_response_time_ms: int
    accuracy: float
    recent_avg_response_time_ms: int
    recent_accuracy: float
    correct_streak: int
