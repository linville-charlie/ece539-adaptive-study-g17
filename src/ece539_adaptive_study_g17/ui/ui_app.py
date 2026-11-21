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
"""Main access point for the UI and driver of the program."""

from tkinter import Tk

from ece539_adaptive_study_g17.database.database_controller import DatabaseController
from ece539_adaptive_study_g17.questions.question_controller import QuestionController
from ece539_adaptive_study_g17.ui.concepts import ConceptManagementUIComponent
from ece539_adaptive_study_g17.ui.questioning import QuestioningUIComponent


class UIApp(Tk):
    """The base UI application that manages the display of other UI components."""

    __concept_management_component: ConceptManagementUIComponent
    __database_controller: DatabaseController
    __questioning_component: QuestioningUIComponent
    __question_controller: QuestionController

    def __init__(
        self,
        question_controller: QuestionController,
        database_controller: DatabaseController,
    ) -> None:
        """Create the UI manager."""
        super().__init__()
        self.__question_controller = question_controller
        self.__database_controller = database_controller
        self.__questioning_component = QuestioningUIComponent(
            question_controller=self.__question_controller,
        )
        self.__concept_management_component = ConceptManagementUIComponent(
            database_controller=self.__database_controller,
        )

    def run(self) -> None:
        """Execute the application."""
        raise NotImplementedError  # TODO
