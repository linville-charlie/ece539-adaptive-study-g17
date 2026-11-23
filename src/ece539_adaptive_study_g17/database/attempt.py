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
"""An attempt to answer a question on a specific concept."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ece539_adaptive_study_g17.database import ATTEMPT_TABLE, CONCEPT_TABLE_ID
from ece539_adaptive_study_g17.database.base_table import _BaseDatabaseTable

if TYPE_CHECKING:
    from ece539_adaptive_study_g17.database.concept import Concept


class Attempt(_BaseDatabaseTable):
    """A particular attempt to answer a question on a given concept."""

    __tablename__ = ATTEMPT_TABLE

    __table_args__ = (
        Index("ix_attempt_table_concept_id_timestamp_ms", "concept_id", "timestamp_ms"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp_ms: Mapped[int] = mapped_column()
    response_time_ms: Mapped[int] = mapped_column()
    was_correct: Mapped[bool] = mapped_column()

    concept_id: Mapped[int] = mapped_column(
        ForeignKey(CONCEPT_TABLE_ID, ondelete="CASCADE")
    )
    concept: Mapped["Concept"] = relationship(back_populates="attempts")  # noqa: UP037
