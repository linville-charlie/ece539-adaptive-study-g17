"""An individual cell in a concept."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from database.concept import Concept
    from database.field import FieldColumn


class Fact:
    """An individual cell in a concept."""

    __tablename__ = "field_column_table"

    concept_id: Mapped[int] = mapped_column(
        ForeignKey("concept_table.id"), primary_key=True
    )
    concept: Mapped["Concept"] = relationship(back_populates="facts")

    field_column_id: Mapped[int] = mapped_column(
        ForeignKey("field_column_table.id"), primary_key=True
    )
    field_column: Mapped["FieldColumn"] = relationship(back_populates="facts")

    fact_data: Mapped[bytes | None] = mapped_column()
