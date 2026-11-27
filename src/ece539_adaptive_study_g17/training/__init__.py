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
"""Prepare EdNet histories for concept-selection training.

Extract learner CSVs, split learners into training/validation/test groups, and
store their attempts using the shared database schema. Export historical concept
features separately from correctness labels, using only answers available before
each question. These tools prepare data; they do not train or change the LSTM.
"""
