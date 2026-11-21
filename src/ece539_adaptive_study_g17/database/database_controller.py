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
"""Interact with the local sqlite database using `sqlalchemy`."""

import sqlite3

from sqlalchemy import Engine, event
from sqlalchemy.pool import ConnectionPoolEntry

# noqa'd imports required for the tables to be created properly.
from ece539_adaptive_study_g17.database.attempt import Attempt  # noqa: F401
from ece539_adaptive_study_g17.database.base_table import _BaseDatabaseTable
from ece539_adaptive_study_g17.database.concept import Concept, ConceptEvaluationData
from ece539_adaptive_study_g17.database.fact import Fact  # noqa: F401
from ece539_adaptive_study_g17.database.field import Field, FieldColumn  # noqa: F401


class DatabaseController:
    """Interact with the local sqlite database using `sqlalchemy`."""

    def __init__(self, engine: Engine) -> None:
        """Create the tables if missing and enforce foreign keys."""
        self._engine = engine
        event.listen(engine, "connect", self._enable_foreign_keys)
        _BaseDatabaseTable.metadata.create_all(engine)

    @staticmethod
    def _enable_foreign_keys(
        dbapi_connection: sqlite3.Connection, _connection_record: ConnectionPoolEntry
    ) -> None:
        """Turn on FK enforcement; SQLite defaults it off, per connection."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def get_concept_by_id(self, id: int) -> Concept:
        """Return a Concept to for question generation and answer evaluation."""
        raise NotImplementedError  # TODO

    def get_concepts_for_selection(self) -> list[ConceptEvaluationData]:
        """Return data on all concepts for concept selection."""
        raise NotImplementedError  # TODO
