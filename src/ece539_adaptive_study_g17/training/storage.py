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
# - Aniketh Kancherla
#
# This file header was last modified 27 Nov 2026.
"""Store EdNet observations using the application's existing ORM tables.

The app has no learner column: each learner must get a separate database.
Source JSONL retains question identity, presentation time, and multi-tag grouping.
"""

from collections.abc import Sequence
from pathlib import Path
from sqlite3 import Connection

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import ConnectionPoolEntry

from ece539_adaptive_study_g17.database.attempt import Attempt
from ece539_adaptive_study_g17.database.base_table import _BaseDatabaseTable
from ece539_adaptive_study_g17.database.concept import Concept
from ece539_adaptive_study_g17.database.field import Field

from .records import TrainingEvent

FEATURE_NAMES = (
    "attempt_count",
    "avg_response_time_ms",
    "accuracy",
    "recent_avg_response_time_ms",
    "recent_accuracy",
    "correct_streak",
)


def write_database(
    path: Path,
    events: Sequence[TrainingEvent],
    concept_map: dict[str, int],
) -> int:
    """Write one learner; return stored attempt count, which may exceed questions.

    A k-tag question creates k attempts because Attempt has one concept_id. These
    are linked by the source JSONL event, never k independent question events.
    No invented question text, facts, learner table, or feature values are stored.
    Summary computation remains owned by Concept.get_evaluation_data().
    """
    if path.exists():
        raise FileExistsError(path)
    if not events:
        message = "learner history must not be empty"
        raise ValueError(message)
    expected_learner_id = events[0].learner_id
    for event_record in events:
        if event_record.learner_id != expected_learner_id:
            message = "all database events must belong to the same learner"
            raise ValueError(message)
    engine = create_engine("sqlite:///" + str(path))

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(
        connection: Connection,
        _record: ConnectionPoolEntry,
    ) -> None:
        # Tell SQLite to enforce links between attempts, concepts, and fields.
        connection.execute("PRAGMA foreign_keys=ON")

    try:
        # Create the shared tables, then save all rows in one transaction.
        _BaseDatabaseTable.metadata.create_all(engine)
        with Session(engine) as session, session.begin():
            field = Field(id=1, name="EdNet English")
            session.add(field)
            # Create each concept once before writing its attempts.
            concept_ids = set()
            for event_record in events:
                for concept_id in event_record.concept_ids:
                    concept_ids.add(concept_id)

            concepts = {}
            for concept_id in sorted(concept_ids):
                concept = Concept(id=concept_map[concept_id], field=field)
                concepts[concept_id] = concept
                session.add(concept)

            attempt_count = 0
            for event_record in events:
                for concept_id in event_record.concept_ids:
                    attempt_count += 1
                    attempt = Attempt(
                        id=attempt_count,
                        concept=concepts[concept_id],
                        timestamp_ms=event_record.timestamp_ms,
                        response_time_ms=event_record.response_time_ms,
                        was_correct=event_record.correct,
                    )
                    session.add(attempt)
        return attempt_count
    finally:
        # Close database resources even if a write fails.
        engine.dispose()
