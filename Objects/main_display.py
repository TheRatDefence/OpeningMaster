import sys
import pygame as p
import pygame_gui as pg
from Objects.interfaces import Screen


#---------------------------------------------------------------------------------------------------#

class MainDisplay:
    # ---------| Static Methods |-------- #
    @staticmethod
    def _new_display_surface(window_size: tuple[int, int]) -> p.Surface:
        """
        Creates a new display
        :param window_size: The size of the window as a tuple
        """
        return p.display.set_mode(window_size).convert_alpha()

    @staticmethod
    def _new_display_ui_manager(window_size: tuple[int, int]) -> pg.UIManager:
        """
        Creates a new UIManager
        :param window_size: The size of the window as a tuple
        """
        return pg.UIManager(window_size)

    @staticmethod
    def _build_screens():
        """
        Initialises each screen registered to the Screen interface
        :return:
        """
        registry = Screen.get_registry()

        screen_map: dict[str, Screen] = {}

        for name, screen_class in registry.items():
            screen_map[name] = screen_class()

        return screen_map



    # -----------| Properties |---------- #
    # TODO(): Add doc strings
    @property
    def running(self) -> bool:
        return self._running

    @running.setter
    def running(self, state: bool):
        if self._running is state:        # running: true -> true or false -> false
            return

        if self._running and not state:   # running: true -> false
            self.shutdown()
            self._running = False
            return

        if not self._running and state:       # running: false -> true
            self._running = True          # Design decision: The main thread will be blocked from this point by a while loop in game_loop()
            self.game_loop()
            return


    # -----------| Methods |------------- #
    def __init__(self, window_size: tuple[int, int], framerate: int):
        """
        The main display. Handles the window and all screens.

        :param window_size: The size of the window as a tuple
        :param framerate: The framerate as an integer
        """
        p.init()

        self._window_surface: p.Surface  = self._new_display_surface(window_size).convert_alpha()
        self._ui_manager: pg.UIManager   = self._new_display_ui_manager(window_size)

        self.framerate: int             = framerate
        self.clock: p.time.Clock        = p.time.Clock()

        self.active_screen: Screen | None   = None # TODO(SP: Default screen): Replace hardcoded "dashboard" with a decorator-based default screen mechanism
        self._screen_map: dict[str, Screen] = self._build_screens()

        self._running: bool = False

    def retrieve_screen_instance(self, screen_name: str) -> Screen:
        """
        Returns an instance of the given screen_name.
        Should be called inside a try-except loop encase the given screen_name doesn't exist.
        :param screen_name: The screen name to search for an instance of.
        :return: A screen or a value error
        """
        if screen_name in self._screen_map.keys():
            return self._screen_map[screen_name]
        else:
            raise ValueError("Screen name does not exist")


    def render_to_display(self, screen_surface: p.Surface) -> None:
        """
        Renders a surface to the main display
        :param screen_surface: The surface to be blit onto the window
        """
        # TODO(SP: Screen border): Add configurable screen border/letterbox rendering

        self._window_surface.blit(screen_surface, dest=(0, 0)) # May need to make dest change-able encase a screen wants to display to a certain location
        self._ui_manager.draw_ui(self._window_surface)

        return

    def game_loop(self) -> None:
        """
        The main game loop. Runs every frame and blocks the main thread.
        Start by setting MainDisplay().running = True
        """

        while self._running:
            # 1. tick the clock
            delta: int = self.clock.tick(self.framerate) # Delta is the time between current frame and last frame

            # 2. process events
            for event in p.event.get():
                match event.type:
                    case p.QUIT:
                        self._running = False

                self.active_screen.handle_event(event)
                self._ui_manager.process_events(event)

            self._ui_manager.update(delta)

            # 3. update active screen
            update_value = self.active_screen.update(delta) # Update value is either a string (new screen name) or None
            if update_value: # Active screen has returned a screen name
                try:
                    screen_instance = self.retrieve_screen_instance(update_value)
                    self.transition_screens(screen_instance)

                except ValueError as e: # Screen name could not be found within map of instantiated screen
                    # TODO(SP: Error handling): Design and implement an error screen instead of silent pass
                    pass

            # 4. render active screen
            self.render_to_display(self.active_screen.render())

            # 5. flip the display
            p.display.flip()

        return

    def transition_screens(self, new_screen: Screen):
        """
        Transitions the active screen to a new one
        :param new_screen: The screen replacing the previous one
        :return:
        """
        self.active_screen = new_screen

    def shutdown(self) -> None:
        """
        Shuts down the app and exits cleanly.
        """
        print("Quiting...")

        p.quit()
        sys.exit()






#---------------------------------------------------------------------------------------------------#
