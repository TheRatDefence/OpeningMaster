from abc import ABC, abstractmethod
import pygame as p
import pygame_gui as pg
from data.database import DatabaseManager


#---------------------------------------------------------------------------------------------------#
#                                   AppState Singleton                                             #
#---------------------------------------------------------------------------------------------------#

class AppState:
    _instance: "AppState | None" = None
    _initialised: bool = False

    def __new__(cls, db=None, opening_id=None):
        if not AppState._instance:
            AppState._instance = super().__new__(cls)
        return AppState._instance

    def __init__(self, db: DatabaseManager | None = None, opening_id: int | None = None):
        """Initialises the app's shared state — db connection and selected opening."""
        if not AppState._initialised:
            if db:
                self.db: DatabaseManager = db
            self.selected_opening_id: int | None = opening_id
            AppState._initialised = True

#---------------------------------------------------------------------------------------------------#
#                                    Screen Interface                                              #
#---------------------------------------------------------------------------------------------------#

class Screen(ABC):
    """An interface that all screens must implement."""

    _registry: dict[str, "type[Screen]"] = {}

    @staticmethod
    def register_screen(screen_name: str):
        """Decorator that registers a Screen subclass under the given name."""
        def decorator(subclass: type[Screen]):
            Screen._registry[screen_name] = subclass
            return subclass
        return decorator

    @staticmethod
    def get_registry() -> dict[str, "type[Screen]"]:
        return Screen._registry

    @property
    def local_screen_surface(self) -> p.Surface:
        return self._screen_surface

    @property
    def local_ui_manager(self) -> pg.UIManager:
        return self._ui_manager

    @abstractmethod
    def render(self) -> p.Surface:
        """Draws and returns the screen surface. Must be implemented by subclasses."""
        ...

    @abstractmethod
    def on_enter(self) -> None:
        """Called when the screen becomes active."""
        ...

    def __init__(self):
        window_size = self.window_size

        self._screen_surface: p.Surface = p.Surface(window_size).convert_alpha()

        import os
        theme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "theme.json")
        if os.path.exists(theme_path):
            self._ui_manager: pg.UIManager = pg.UIManager(window_size, theme_path)
        else:
            self._ui_manager: pg.UIManager = pg.UIManager(window_size)

        self.state = AppState()

    def handle_event(self, event: p.event.Event) -> None:
        """Passes event to the UI manager. Override and call super() for screen-specific handling."""
        self.local_ui_manager.process_events(event)
        return None

    def update(self, delta_ms: int) -> str | None:
        """Called each frame. Return a screen name string to trigger a transition, or None to stay."""
        self.local_ui_manager.update(delta_ms)
        return None

    @property
    def window_size(self) -> tuple[int, int]:
        """Returns the window dimensions. Only valid after MainDisplay is initialised."""
        display = p.display.get_surface()

        if display:
            return display.get_size()
        else:
            raise Exception("A MainDisplay instance must be initialised before initialising screens")

    @staticmethod
    def panel_pct_rect(panel: pg.elements.UIPanel, x: float, y: float, w: float, h: float) -> p.Rect:
        """Returns a rect as percentages relative to a UIPanel's inner dimensions."""
        p_rect = panel.get_container().get_rect()
        pw, ph = p_rect.width, p_rect.height

        return p.Rect(pw * x, ph * y, pw * w, ph * h)

    def pct_rect(self, x: float, y: float, w: float, h: float) -> p.Rect:
        """Returns a rect as percentages of the window size."""
        w_width, w_height = self.window_size

        return p.Rect(w_width * x,
                      w_height * y,
                      w_width * w,
                      w_height * h)