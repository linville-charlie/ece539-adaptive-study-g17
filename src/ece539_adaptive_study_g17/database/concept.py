"""Manages database and project concepts."""

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
        """Get the historic data for use in selection."""
        raise NotImplementedError  # TODO


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
