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
