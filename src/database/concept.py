"""Manages database and project concepts."""

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base_table import _BaseDatabaseTable
from database.fact import Fact

if TYPE_CHECKING:
    from database.field import Field


class Concept(_BaseDatabaseTable):
    """Represents a group of related informaiton."""

    __tablename__ = "concept_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    # TODO Add training data (accuracy, recent accuracy, etc.)

    field_id: Mapped[int] = mapped_column("field_table.id")
    field: Mapped["Field"] = relationship()

    facts: Mapped[list["Fact"]] = relationship(back_populates="concept")

    def get_evaluation_data(self) -> ConceptEvaluationData:
        """Get the historic data for use in selection."""


class ConceptEvaluationData:
    """The data stored in a concept that the selector uses to evaluate it."""
