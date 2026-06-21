import pygame as p
import pygame_gui as pg

from core.infrastructure import Screen

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

    def render(self) -> p.Surface:
        # TODO(): Replace placeholders with actual UI
        screen = self._screen_surface
        ui = self._ui_manager

        text_colour = (0, 0, 0)
        bg_colour = (255, 255, 255)
        screen.fill(bg_colour)

        font = p.font.SysFont(None, 36)
        text = font.render("Dashboard Screen - Placeholder", True, text_colour)

        screen.blit(text, (0, 0))
        ui.draw_ui(screen)
        return self._screen_surface
