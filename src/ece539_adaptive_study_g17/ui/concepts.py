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
"""UI elements for the management of concepts by the user."""

from tkinter import Frame

from ece539_adaptive_study_g17.database.database_controller import DatabaseController


class ConceptManagementUIComponent(Frame):
    """Main UI element for the management of concepts by the user.

    It is able to:
    - Create, view, update, and delete fields;
    - Add and remove field columns;
    - Add and remove concepts;
    - Edit (including possible removal) of facts in concepts.
    """

    # Saving, undo/redo recommended, but do what's possible.
    # Probably make this just the UI component rather than a unified view/controller
    #   setup.

    _database_controller: DatabaseController

    def __init__(self, database_controller: DatabaseController) -> None:
        """Create a concept management UI component."""
        super().__init__()
        raise NotImplementedError  # TODO
