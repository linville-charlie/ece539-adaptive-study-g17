"""An individual cell in a concept."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import CONCEPT_TABLE_ID, FACT_TABLE, FIELD_COLUMN_TABLE_ID

if TYPE_CHECKING:
    from database.concept import Concept
    from database.field import FieldColumn


class Fact:
    """An individual cell in a concept."""

    __tablename__ = FACT_TABLE

    concept_id: Mapped[int] = mapped_column(
        ForeignKey(CONCEPT_TABLE_ID), primary_key=True
    )
    concept: Mapped["Concept"] = relationship(back_populates="facts")

    field_column_id: Mapped[int] = mapped_column(
        ForeignKey(FIELD_COLUMN_TABLE_ID), primary_key=True
    )
    field_column: Mapped["FieldColumn"] = relationship(back_populates="facts")

    fact_data: Mapped[bytes | None] = mapped_column()
