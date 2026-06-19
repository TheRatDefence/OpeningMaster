from abc import ABC, abstractmethod
import pygame
import pygame_gui


#---------------------------------------------------------------------------------------------------#

class Screen(ABC):
    """
    An interface that all screens must implement in order to be used in the main game loop.
    """

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