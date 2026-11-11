"""Manages database and project concepts."""

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base_table import _BaseDatabaseTable
from database.fact import Fact

if TYPE_CHECKING:
    from database.field import Field


class Concept(_BaseDatabaseTable):
    """Represents a group of related informaiton."""

    __tablename__ = "concept"

    id: Mapped[int] = mapped_column(primary_key=True)
    field: Mapped["Field"] = relationship("Field")
    facts: Mapped[list["Fact"]] = relationship(
        "Fact",
        back_populates="Concept",
        cascade="all,delete-orphans",
    )
    # TODO Add training data (accuracy, recent accuracy, etc.)
