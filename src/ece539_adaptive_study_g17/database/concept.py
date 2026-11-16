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
    last_attempt_timestamp: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True)
    )

    field_id: Mapped[int] = mapped_column(ForeignKey(FIELD_TABLE_ID))
    field: Mapped[Field] = relationship()

    facts: Mapped[list[Fact]] = relationship(back_populates="concept")

    def get_evaluation_data(self) -> ConceptEvaluationData:
        """Get the historic data for use in selection."""
        raise NotImplementedError  # TODO


class Attempt(_BaseDatabaseTable):
    """A particular attempt to answer a question on a given concept."""

    concept_id: Mapped[int] = mapped_column(
        ForeignKey("concept.id", ondelete="CASCADE"), index=True
    )
    timestamp_ms: Mapped[int] = mapped_column(index=True)
    response_time_ms: Mapped[int]
    was_correct: Mapped[bool]


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
