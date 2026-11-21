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
"""Uses the trained model to select the next question."""

from ece539_adaptive_study_g17.database.concept import Concept, ConceptEvaluationData


class ConceptSelector:
    """Uses the trained model to select the next question."""

    # TODO This should be a mock class until we can hook in the model.

    def __init__(self) -> None:
        """Create a question selector."""
        raise NotImplementedError  # TODO

    def select_concept(self, concept_eval_data: list[ConceptEvaluationData]) -> Concept:
        """Select a concept to build a question around."""
        raise NotImplementedError  # TODO
