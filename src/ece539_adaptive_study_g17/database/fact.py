"""An individual cell in a concept."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ece539_adaptive_study_g17.database import (
    CONCEPT_TABLE_ID,
    FACT_TABLE,
    FIELD_COLUMN_TABLE_ID,
)
from ece539_adaptive_study_g17.database.base_table import _BaseDatabaseTable

if TYPE_CHECKING:
    from ece539_adaptive_study_g17.database.concept import Concept
    from ece539_adaptive_study_g17.database.field import FieldColumn


class Fact(_BaseDatabaseTable):
    """An individual cell in a concept."""

    __tablename__ = FACT_TABLE

    concept_id: Mapped[int] = mapped_column(
        ForeignKey(CONCEPT_TABLE_ID, ondelete="CASCADE"), primary_key=True
    )
    concept: Mapped[Concept] = relationship(back_populates="facts")

    field_column_id: Mapped[int] = mapped_column(
        ForeignKey(FIELD_COLUMN_TABLE_ID, ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    field_column: Mapped[FieldColumn] = relationship(back_populates="facts")

    value_str: Mapped[str | None] = mapped_column()
    value_blob: Mapped[bytes | None] = mapped_column()
