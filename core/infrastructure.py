from abc import ABC, abstractmethod
import pygame as p
import pygame_gui as pg
from data.database import DatabaseManager


#----------------------------------------|  AppState Singleton  |----------------------------------#

class AppState:
    # --------------------| Class Level Variables |-------------------- #
    _instance: "AppState | None" = None     # Forward reference
    _initialised: bool = False

    # --------------------|    Singleton Logic    |-------------------- #
    def __new__(cls, db=None, opening_id=None):
        """
        Called before __init__ to check if an instance already exists.
        Creates a new instance if none exists or returns the existing one.
        """

        if not AppState._instance:                      # No singleton instance yet
            AppState._instance = super().__new__(cls)   # Initialises new AppState instance and avoids infinite loop

        return AppState._instance                       # Always return the object stored in _instance

    def __init__(self, db: DatabaseManager | None = None, opening_id: int | None = None):
        """
        Stores the running state as a singleton object to be shared between screens.
        Calling AppState() only creates a new instance if none exist,
        otherwise returning the existing one.
        :param db: The database manager
        :param opening_id: The selected opening id
        """

        # __init__ gets called everytime AppState() is called, even if __new__ returns an existing instance
        if not AppState._initialised:                           # The singleton hasn't been initialised yet
            if db: self.db: DatabaseManager = db                # Don't change self.db if db is None
            self.selected_opening_id: int | None = opening_id   # Always set selected_opening_id to opening_id

            AppState._initialised = True

#-----------------------------------------| Screen Interface |--------------------------------------#

class Screen(ABC):
    """
    An interface that all screens must implement in order to be used in the main game loop.
    """

    # ----------| Registry |---------- #
    _registry: dict[str, "type[Screen]"] = {}   # Have to resolve the Screen forward reference using a string literal

    @staticmethod
    def register_screen(screen_name: str):
        """
        A decorator that registers classes that are to be built by MainDisplay
        :param screen_name: The name of the screen as a string (used when transitioning screens)
        """
        def decorator(subclass: type[Screen]):
            Screen._registry[screen_name] = subclass
            return subclass
        return decorator

    @staticmethod
    def get_registry() -> dict[str, "type[Screen]"]:    # Another forward reference
        """
        Retrieves the registry of screens
        :return: dict[str, type[Screen]]
        """
        return Screen._registry

   # ---------| Properties |--------- #
    @property
    def local_screen_surface(self) -> p.Surface:
        """
        :return: The local screen surface
        """
        return self._screen_surface

    @property
    def local_ui_manager(self) -> pg.UIManager:
        """
        :return: The local UIManager
        """
        return self._ui_manager

    # ---------| Abstract Methods |------------ #
    @abstractmethod
    def render(self) -> p.Surface:
        """
        Draws the screen. Must be defined by Screen classes
        :return: Returns the drawn screen
        """
        ...

    @abstractmethod
    def on_enter(self) -> None:
        """
        Called by the MainDisplay whenever a screen becomes active.
        """
        ...

    # ---------| Inheritable |------------ #
    def __init__(self):
        window_size = self.window_size

        self._screen_surface: p.Surface = p.Surface(window_size).convert_alpha()
        self._ui_manager: pg.UIManager  = pg.UIManager(window_size)

    def handle_event(self, event: p.event.Event) -> None:
        """
        Base Behaviour: pass the event to local_ui_manager.
        Override and call super() to add screen-specific event handling.
        :param event: The pygame event
        :return: None
        """
        self.local_ui_manager.process_events(event)
        return None

    def update(self, delta_ms: int) -> str |None:
        """
        Base Behaviour: pass delta_ms to local_ui_manager.
        Override and call super() to add screen-specific update handling.
        :param delta_ms: The time since last update call
        :return: None or a string to trigger a screen transition
        """
        self.local_ui_manager.update(delta_ms)
        return None

    @property
    def window_size(self) -> tuple[int, int]: # Important design decision: All screens need the window size, but shouldn't be able to access the main surface directly.
        """
        Returns the surface size of the window instantiated from MainDisplay.
        Warning: Only call after initialising a MainDisplay
        :return: tuple[int, int]
        """
        display = p.display.get_surface()

        if display:
            return display.get_size()
        else:
            raise Exception("A MainDisplay instance must be initialised before initialising screens")

#---------------------------------------------------------------------------------------------------#