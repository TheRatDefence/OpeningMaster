import pygame as p
import pygame_gui as pg
from Objects.interfaces import Screen

@Screen.register_screen("dashboard")
class DashboardScreen(Screen):
    def __init__(self):
        """
        The dashboard Screen
        """
        window_size = self.window_size

        self._screen_surface: p.Surface = p.Surface(window_size).convert_alpha()
        self._ui_manager: pg.UIManager  = pg.UIManager(window_size)

    # ---------| Properties |--------- #
    @property
    def local_screen_surface(self) -> p.Surface:
        return self._screen_surface

    @property
    def local_ui_manager(self) -> pg.UIManager:
        return self._ui_manager


    # ---------| Methods |------------ #
    def handle_event(self, event: p.event.Event) -> None:
        self._ui_manager.process_events(event)
        return None

    def update(self, delta_ms: int) -> str | None:
        # TODO(): Finish implementing
        return None

    def render(self) -> p.Surface:
        # TODO(): Replace placeholders with actual UI
        screen = self._screen_surface

        text_colour = (0, 0, 0)
        bg_colour = (255, 255, 255)
        screen.fill(bg_colour)

        font = p.font.SysFont(None, 36)
        text = font.render("Dashboard Screen - Placeholder", True, text_colour)

        screen.blit(text, (0, 0))
        return self._screen_surface # does the same as returning screen right?
