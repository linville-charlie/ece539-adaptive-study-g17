#   539g17 Adaptive Study Integration Project
#   Copyright (C) 2026  A. Kancherla, C. Linville, Q. Schultz, E. Wulf.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Authors of this file:
#
# - Quentin Schultz
#
# This file header was last modified 21 Nov 2026.
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
