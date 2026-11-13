"""UI elements for the management of concepts by the user."""

from tkinter import Tk, Widget

from database.database_controller import DatabaseController


class ConceptManagementUIComponent(Widget):
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

    __database_controller: DatabaseController

    def __init__(
        self, parent: Widget | Tk, name: str, database_controller: DatabaseController
    ) -> None:
        """Create a concept management UI component."""
        super().__init__(master=parent, widgetName=name)
