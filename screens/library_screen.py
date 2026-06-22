import pygame as p
import pygame_gui as pg

from core.infrastructure import Screen
from core.infrastructure import AppState

@Screen.register_screen("library")
class LibraryScreen(Screen):
    def __init__(self):
        """
        The library screen. Displays openings and allows the user to select one.

        Features:
        1. Opening list (left panel) — fetch all openings from AppState().db.get_all_openings() and display them as a scrollable list. Clicking one selects it.
        2. Move sequence (right panel) — when an opening is selected, display its move sequence. The PGN is stored in the database — you'll need python-chess to parse it into a readable list of moves.
        3. Practice button — a button that sets AppState().selected_opening_id to the currently selected opening, then returns "practice" from update() to trigger the screen transition.
        """
        super().__init__()

        self._openings_dict: list[dict] = self.state.db.get_all_openings()
        self._openings_list: pg.elements.UISelectionList = self.create_opening_list()

        self._selected_opening: dict | None = None

        self._right_panel_container: pg.elements.UIPanel = self.refresh_right_panel()

        self._transition = False

    # -----------------| Helper Methods |----------------- #

    def create_opening_list(self) -> pg.elements.UISelectionList:
        """
        Turns the list of opening rows into a scrollable UI element
        :return: pygame_gui.elements.UISelectionList
        """
        openings = self._openings_dict

        item_list = [opening["name"] for opening in openings]   # Get a list of each opening's name

        # TODO(): Address these magic numbers
        rect = self.pct_rect(0, 0.05, 0.4, 0.9)     # Create a rectangle for the openings to sit on

        return pg.elements.UISelectionList( item_list=item_list,
                                            manager=self.local_ui_manager,
                                            relative_rect=rect )

    def create_practice_button(self, panel: pg.elements.UIPanel) -> pg.elements.UIButton:
        """
        Creates a practice button
        :param panel: The parent (right panel) container
        :return: A practice button
        """

        rect = self.panel_pct_rect(panel, 0.05, 0.85, 0.9, 0.10)

        return pg.elements.UIButton( relative_rect=rect,
                                     manager=self.local_ui_manager,
                                     text="Practice",
                                     container=panel,
                                     command=lambda: setattr(self, '_transition', True))    # Set the transition flag True if clicked

    def create_move_list(self, panel: pg.elements.UIPanel) -> pg.elements.UITextBox:
        """
        Creates a text box displaying the currently selected opening's move list
        :param panel: The parent (right panel) container
        :return: A moves text box
        """
        opening = self._selected_opening
        if not opening:
            raise ValueError("No opening selected")

        rect = self.panel_pct_rect(panel, 0.05, 0.05, 0.9, 0.75)

        moves: str = opening["pgn"]

        return pg.elements.UITextBox( relative_rect=rect,
                                      manager=self.local_ui_manager,
                                      html_text=moves,
                                      container=panel )

    def refresh_right_panel(self) -> pg.elements.UIPanel:
        """
        Kills previous elements on the right panel and recreates them.
        :return:
        """
        if hasattr(self, "_right_panel_container"):         # Check if panel exists already
            self._right_panel_container.kill()

        rect = self.pct_rect(0.4, 0.05, 0.6, 0.9)
        new_panel = pg.elements.UIPanel( relative_rect=rect,
                                         manager=self.local_ui_manager,
                                         margins={'left': 10, 'right': 10, 'top': 10, 'bottom': 10} )

        if self._selected_opening:
            self.create_practice_button(new_panel)
            self.create_move_list(new_panel)

        return new_panel




    # -----------------| Event Methods |----------------- #

    def select_opening_from_name(self, name: str) -> None:
        """
        Finds the dict and sets self._selected_opening to the dict then sets AppState.selected_opening_id
        :param name: The name of the opening
        """
        openings_dict   = self._openings_dict

        opening = next(opening for opening in openings_dict
                          if name == opening["name"])

        if not isinstance(opening, dict):
            raise ValueError("Name does not exist within list of openings")

        self._selected_opening          = opening
        self.state.selected_opening_id  = opening["id"]

        return None

    # -----------------| Game Loop Methods |----------------- #

    def on_enter(self) -> None:
        self._openings_dict = AppState().db.get_all_openings()    # Updates the list of openings each time screen becomes active
        return None

    def handle_event(self, event: p.event.Event) -> None:
        super().handle_event(event)                               # Handle event with local UIManager

        match event.type:
            # --------------------| Opening list was clicked |-------------------- #
            case pg.UI_SELECTION_LIST_NEW_SELECTION:
                name_clicked = event.text
                self.select_opening_from_name(name_clicked)
                self.refresh_right_panel()

        return None

    def update(self, delta_ms: int) -> str |None:
        super().update(delta_ms)

        if self._transition:
            self._transition = False
            return "practice"

        return None

    def render(self) -> p.Surface:
        screen = self.local_screen_surface
        ui = self.local_ui_manager

        # TODO(): Theming / colour scheme
        background_colour = (255, 0, 0)

        screen.fill(background_colour)
        ui.draw_ui(screen)
        return screen