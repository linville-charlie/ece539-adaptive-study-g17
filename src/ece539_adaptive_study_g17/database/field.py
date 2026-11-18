"""The structure into which concepts and their facts are embedded."""

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ece539_adaptive_study_g17.database import (
    FIELD_COLUMN_TABLE,
    FIELD_TABLE,
    FIELD_TABLE_ID,
)
from ece539_adaptive_study_g17.database.base_table import _BaseDatabaseTable

if TYPE_CHECKING:
    from ece539_adaptive_study_g17.database.fact import Fact


class Field(_BaseDatabaseTable):
    """A collection of typed columns all concepts in this field have."""

    __tablename__ = FIELD_TABLE
    __table_args__ = (UniqueConstraint("name", name="uq_field_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)

    field_columns: Mapped[list[FieldColumn]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DataType(Enum):
    """A data type stored in a concept."""

    Numeric = 0
    Boolean = 1
    Text = 2
    Image = 3


class FieldColumn(_BaseDatabaseTable):
    """A column of data in a given field."""

    __tablename__ = FIELD_COLUMN_TABLE
    __table_args__ = (
        UniqueConstraint("field_id", "name", name="uq_field_column_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    data_type: Mapped[DataType] = mapped_column(
        SQLEnum(
            DataType,
            create_constraint=True,
            native_enum=False,
        )
    )
    enforce_uniqueness: Mapped[bool] = mapped_column()
    required: Mapped[bool] = mapped_column()

    field_id: Mapped[int] = mapped_column(
        ForeignKey(FIELD_TABLE_ID, ondelete="CASCADE"), index=True, nullable=False
    )
    field: Mapped[Field] = relationship(back_populates="field_columns")

    facts: Mapped[list[Fact]] = relationship(
        back_populates="field_column",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
