import pygame as p
import pygame_gui as pg

from core.infrastructure import Screen

@Screen.register_screen("dashboard")
class DashboardScreen(Screen):
    def __init__(self):
        """The dashboard screen."""
        super().__init__()

    def on_enter(self) -> None:
        pass

    def render(self) -> p.Surface:
        # TODO(): Replace placeholders with actual UI
        screen = self._screen_surface
        ui = self._ui_manager

        text_colour = (0, 0, 0)
        bg_colour = (255, 255, 255)
        screen.fill(bg_colour)

        font = p.font.SysFont(None, 48)
        text = font.render("Dashboard Screen - Placeholder", True, text_colour)

        screen.blit(text, (0, 0))
        ui.draw_ui(screen)
        return self._screen_surface
