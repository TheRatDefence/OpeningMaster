import pygame as p
import pygame_gui as pg
from interfaces import Screen


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
        if self._running != state:        # running: true -> true or false -> false
            return

        if self._running and not state:   # running: true -> false
            self.shutdown()
            self._running = False
            return

        if self._running and state:       # running: false -> true
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

        self.active_screen: Screen | None   = None # TODO(): Determine how the default screen will be picked (maybe through a decorator)
        self._screen_map: dict[str, Screen] = self._build_screens()

        self._running: bool = False


    def game_loop(self):
        # TODO(): Implement the game_loop logic
        while self._running:
            # 1. tick the clock
            delta: int = self.clock.tick(self.framerate) # Delta is the time between current frame and last frame

            # 2. process events
            for event in p.event.get():
                self.active_screen.handle_event(event) # Will fix active_screen maybe None when


            # 3. update active screen
            # 4. render active screen
            # 5. flip the display


        pass

    def shutdown(self):
        # TODO(): Implement full shutdown + app clean up logic
        pass







#---------------------------------------------------------------------------------------------------#
