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
"""Manages database and project concepts."""

from collections.abc import Sequence
from dataclasses import dataclass
from math import floor, log
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship, selectinload

from ece539_adaptive_study_g17.database import CONCEPT_TABLE, FIELD_TABLE_ID
from ece539_adaptive_study_g17.database.attempt import Attempt
from ece539_adaptive_study_g17.database.base_table import _BaseDatabaseTable
from ece539_adaptive_study_g17.database.fact import Fact

if TYPE_CHECKING:
    from ece539_adaptive_study_g17.database.field import Field

MAX_RECENCY = 50


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
        """Get the historic data for use in selection."""

        def _get_accuracy(attempts: list[Attempt]) -> float:
            return sum([1 if attempt.was_correct else 0 for attempt in attempts]) / len(
                attempts
            )

        def _get_avg_time(attempts: list[Attempt]) -> int:
            return sum([attempt.response_time_ms for attempt in attempts]) // len(
                attempts
            )

        attempt_count = len(self.attempts)

        if attempt_count == 0:
            return ConceptEvaluationData(
                concept_id=self.id,
                attempt_count=0,
                avg_response_time_ms=0,
                accuracy=0,
                recent_avg_response_time_ms=0,
                recent_accuracy=0,
                correct_streak=0,
            )

        recent_attempt_count = min(
            floor(10 * log(attempt_count + 1)), attempt_count, MAX_RECENCY
        )
        recent_attempts = self.attempts[-recent_attempt_count:]
        average_attempt_time = _get_avg_time(self.attempts)
        attempt_accuracy = _get_accuracy(self.attempts)
        recent_attempt_time = _get_avg_time(recent_attempts)
        recent_attempt_accuracy = _get_accuracy(recent_attempts)
        try:
            correct_streak_len = [attempt.was_correct for attempt in self.attempts][
                ::-1
            ].index(False)
        except ValueError:
            correct_streak_len = attempt_count

        return ConceptEvaluationData(
            concept_id=self.id,
            attempt_count=attempt_count,
            avg_response_time_ms=average_attempt_time,
            accuracy=attempt_accuracy,
            recent_avg_response_time_ms=recent_attempt_time,
            recent_accuracy=recent_attempt_accuracy,
            correct_streak=correct_streak_len,
        )

    @classmethod
    def get_all_concepts(cls, session: Session) -> Sequence[Concept]:
        """Return a list of all concepts stored in the database."""
        return session.scalars(
            select(Concept).options(selectinload(Concept.attempts))
        ).all()

    @classmethod
    def get_evaluation_data_for_all_concepts(
        cls, session: Session
    ) -> list[ConceptEvaluationData]:
        """Return the evaluation data (input features) for all concepts."""
        return [
            concept.get_evaluation_data() for concept in cls.get_all_concepts(session)
        ]


@dataclass(frozen=True, slots=True)
class ConceptEvaluationData:
    """The data stored in a concept that the selector uses to evaluate it."""

    concept_id: int
    attempt_count: int
    avg_response_time_ms: int
    accuracy: float
    recent_avg_response_time_ms: int
    recent_accuracy: float
    correct_streak: int
