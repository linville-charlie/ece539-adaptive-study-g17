"""An attempt to answer a question on a specific concept."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ece539_adaptive_study_g17.database import ATTEMPT_TABLE, CONCEPT_TABLE_ID
from ece539_adaptive_study_g17.database.base_table import _BaseDatabaseTable


class Attempt(_BaseDatabaseTable):
    """A particular attempt to answer a question on a given concept."""

    __tablename__ = ATTEMPT_TABLE

    id: Mapped[int] = mapped_column(primary_key=True)
    concept_id: Mapped[int] = mapped_column(
        ForeignKey(CONCEPT_TABLE_ID, ondelete="CASCADE"), index=True
    )
    timestamp_ms: Mapped[int] = mapped_column(index=True)
    response_time_ms: Mapped[int]
    was_correct: Mapped[bool]
