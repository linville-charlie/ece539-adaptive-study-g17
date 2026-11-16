"""Manages database and project concepts."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ece539_adaptive_study_g17.database import CONCEPT_TABLE, FIELD_TABLE_ID
from ece539_adaptive_study_g17.database.base_table import _BaseDatabaseTable
from ece539_adaptive_study_g17.database.fact import Fact

if TYPE_CHECKING:
    from ece539_adaptive_study_g17.database.field import Field


class Concept(_BaseDatabaseTable):
    """Represents a group of related informaiton."""

    __tablename__ = CONCEPT_TABLE

    id: Mapped[int] = mapped_column(primary_key=True)
    # TODO Add training data (accuracy, recent accuracy, etc.)

    field_id: Mapped[int] = mapped_column(ForeignKey(FIELD_TABLE_ID))
    field: Mapped["Field"] = relationship()

    facts: Mapped[list["Fact"]] = relationship(back_populates="concept")

    def get_evaluation_data(self) -> ConceptEvaluationData:
        """Get the historic data for use in selection."""
        raise NotImplementedError  # TODO


class ConceptEvaluationData:
    """The data stored in a concept that the selector uses to evaluate it."""
    # TODO Add training data (accuracy, recent accuracy, etc.)
