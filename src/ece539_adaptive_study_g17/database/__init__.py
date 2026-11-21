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

FIELD_TABLE = "field_table"
CONCEPT_TABLE = "concept_table"
FIELD_COLUMN_TABLE = "field_column_table"
FACT_TABLE = "fact_table"
ATTEMPT_TABLE = "attempt_table"

FIELD_TABLE_ID = FIELD_TABLE + ".id"
CONCEPT_TABLE_ID = CONCEPT_TABLE + ".id"
FIELD_COLUMN_TABLE_ID = FIELD_COLUMN_TABLE + ".id"
ATTEMPT_TABLE_ID = ATTEMPT_TABLE + ".id"
