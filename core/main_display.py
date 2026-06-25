import sys
import pygame as p
import pygame_gui as pg
from core.infrastructure import Screen


#---------------------------------------------------------------------------------------------------#
#                                      MainDisplay                                                 #
#---------------------------------------------------------------------------------------------------#

class MainDisplay:
    @staticmethod
    def _new_display_surface(window_size: tuple[int, int]) -> p.Surface:
        return p.display.set_mode(window_size)

    @staticmethod
    def _new_display_ui_manager(window_size: tuple[int, int]) -> pg.UIManager:
        import os
        theme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "theme.json")
        if os.path.exists(theme_path):
            return pg.UIManager(window_size, theme_path)
        return pg.UIManager(window_size)

    @staticmethod
    def _build_screens():
        registry = Screen.get_registry()
        screen_map: dict[str, Screen] = {}

        for name, screen_class in registry.items():
            screen_map[name] = screen_class()

        return screen_map

    @property
    def running(self) -> bool:
        return self._running

    @running.setter
    def running(self, state: bool):
        if self._running is state:
            return

        if self._running and not state:
            self.shutdown()
            self._running = False
            return

        if not self._running and state:
            self._running = True
            self.game_loop()
            return

    def __init__(self, window_size: tuple[int, int], framerate: int, default_screen: str = "dashboard"):
        """Sets up the window, UI manager, and all registered screens."""
        p.mixer.init()
        p.init()

        self._window_surface: p.Surface  = self._new_display_surface(window_size)
        self._ui_manager: pg.UIManager   = self._new_display_ui_manager(window_size)

        self.framerate: int             = framerate
        self.clock: p.time.Clock        = p.time.Clock()

        self._screen_map: dict[str, Screen] = self._build_screens()
        self.active_screen: Screen          = self.retrieve_screen_instance(default_screen)

        self._running: bool = False
        self._back_button: pg.elements.UIButton | None = None
        self._create_back_button()
        self._update_back_button_visibility()

    def retrieve_screen_instance(self, screen_name: str) -> Screen:
        """Returns the instantiated screen for the given name, or raises ValueError if not found."""
        if screen_name in self._screen_map.keys():
            return self._screen_map[screen_name]
        else:
            raise ValueError("Screen name does not exist")

    def _create_back_button(self) -> None:
        """Creates a back button in the top-left corner."""
        button_rect = p.Rect(10, 10, 120, 50)
        self._back_button = pg.elements.UIButton(
            relative_rect=button_rect,
            text="← Back",
            manager=self._ui_manager
        )

    def render_to_display(self, screen_surface: p.Surface) -> None:
        self._window_surface.blit(screen_surface, dest=(0, 0))
        self._ui_manager.draw_ui(self._window_surface)

    def game_loop(self) -> None:
        """Runs the main loop. Blocks the calling thread until the app shuts down."""
        while self._running:
            delta: int = self.clock.tick(self.framerate)

            for event in p.event.get():
                match event.type:
                    case p.QUIT:
                        self._running = False
                    case pg.UI_BUTTON_PRESSED:
                        if event.ui_element == self._back_button:
                            self.transition_screens(self.retrieve_screen_instance("library"))

                self.active_screen.handle_event(event)
                self._ui_manager.process_events(event)

            self._ui_manager.update(delta)

            update_value = self.active_screen.update(delta)
            if update_value:
                try:
                    screen_instance = self.retrieve_screen_instance(update_value)
                    self.transition_screens(screen_instance)

                except ValueError as e:
                    pass

            screen_surface = self.active_screen.render()
            self.render_to_display(screen_surface)

            p.display.flip()

    def transition_screens(self, new_screen: Screen):
        """Switches the active screen to new_screen."""
        self.active_screen = new_screen
        self.active_screen.on_enter()
        self._update_back_button_visibility()

    def _update_back_button_visibility(self) -> None:
        """Shows back button on all screens except library."""
        if self._back_button is None:
            return

        # Get the current screen name from the registry
        current_screen_name = None
        for name, screen in self._screen_map.items():
            if screen == self.active_screen:
                current_screen_name = name
                break

        if current_screen_name == "library":
            self._back_button.hide()
        else:
            self._back_button.show()

    def shutdown(self) -> None:
        print("Quiting...")
        p.quit()
        sys.exit()


#---------------------------------------------------------------------------------------------------#
