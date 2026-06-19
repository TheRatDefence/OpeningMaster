from abc import ABC, abstractmethod
import pygame
import pygame_gui


#---------------------------------------------------------------------------------------------------#

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
    @abstractmethod
    def local_screen_surface(self) -> pygame.Surface:
        """
        :return: The local screen surface
        """
        ...

    @property
    @abstractmethod
    def local_ui_manager(self) -> pygame_gui.UIManager:
        """
        :return: The local UIManager
        """
        ...


    # ---------| Abstract Methods |------------ #

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Receives one pygame event per call.
        :param event: The pygame event
        :return: None
        """
        ...

    @abstractmethod
    def update(self, delta_ms: float) -> str |None:
        """
        Handles the per-frame logic
        :param delta_ms: The time since last update call
        :return: A string key to trigger a transition or None to stay
        """
        ...

    @abstractmethod
    def render(self) -> pygame.Surface:
        """
        Draws the screen
        :return: Returns the drawn screen
        """
        ...


    # ---------| Inheritable Methods |------------ #

    def handoff(self, last_surface: pygame.Surface, last_UIManager: pygame_gui.UIManager):
        """
        Called by the transition process
        :param last_surface: The surface of the last active screen
        :param last_UIManager: The UIManager used by the last screen
        :return: None
        """

        # TODO: Finish this method



#---------------------------------------------------------------------------------------------------#