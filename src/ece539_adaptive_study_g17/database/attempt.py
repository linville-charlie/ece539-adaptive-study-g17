"""An attempt to answer a question on a specific concept."""

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ece539_adaptive_study_g17.database import ATTEMPT_TABLE, CONCEPT_TABLE_ID
from ece539_adaptive_study_g17.database.base_table import _BaseDatabaseTable
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
    concept: Mapped[Concept] = relationship(back_populates="attempts")
