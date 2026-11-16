"""Manages database and project concepts."""
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ece539_adaptive_study_g17.database import CONCEPT_TABLE, FIELD_TABLE_ID
from ece539_adaptive_study_g17.database.base_table import _BaseDatabaseTable
from ece539_adaptive_study_g17.database.fact import Fact

if TYPE_CHECKING:
    from ece539_adaptive_study_g17.database.field import Field


class Concept(_BaseDatabaseTable):
    """Represents a group of related information."""

    __tablename__ = CONCEPT_TABLE

    id: Mapped[int] = mapped_column(primary_key=True)
    # TODO Confirm training data
    last_attempt_timestamp: Mapped[datetime|None] = mapped_column(
        TIMESTAMP(timezone=True)
    )
    attempt_count: Mapped[int] = mapped_column(default=0)
    avg_response_time_ms: Mapped[float] = mapped_column(default=0)
    accuracy: Mapped[float] = mapped_column(default=0)
    recent_response_times_ms: Mapped[float] = mapped_column(default=0)
    recent_accuracy: Mapped[float] = mapped_column(default=0)
    correct_streak: Mapped[int] = mapped_column(default=0)

    field_id: Mapped[int] = mapped_column(ForeignKey(FIELD_TABLE_ID))
    field: Mapped[Field] = relationship()

    facts: Mapped[list[Fact]] = relationship(back_populates="concept")

    def get_evaluation_data(self) -> ConceptEvaluationData:
        """Get the historic data for use in selection."""
        raise NotImplementedError  # TODO


@dataclass(frozen=True, slots=True)
class ConceptEvaluationData:
    """The data stored in a concept that the selector uses to evaluate it."""

    # TODO Confirm training data
    concept_id: int
    attempt_count: int
    avg_response_time_ms: float
    accuracy: float
    recent_avg_response_time_ms: float
    recent_accuracy: float
    correct_streak: int
