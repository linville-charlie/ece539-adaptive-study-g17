"""The structure into which concepts and their facts are embedded."""

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from database.fact import Fact


class Field:
    """A collection of typed columns all concepts in this field have."""

    __tablename__ = "field_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    field_coulmns: Mapped[FieldColumn] = relationship(back_populates="field")


class FieldColumn:
    """A column of data in a given field."""

    __tablename__ = "field_column_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    data_type: Mapped[DataType] = mapped_column()
    enforce_uniqueness: Mapped[bool] = mapped_column()
    required: Mapped[bool] = mapped_column()

    field_id: Mapped[int] = mapped_column(ForeignKey("field_table"))
    field: Mapped[Field] = relationship(back_populates="field_columns")

    facts: Mapped["Fact"] = relationship(back_populates="field_column")


class DataType(Enum):
    """A data type stored in a concept."""

    Numeric = (0,)
    Boolean = (1,)
    Text = (2,)
    Image = (3,)
