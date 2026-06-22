from core.infrastructure    import AppState
from core.main_display      import MainDisplay
from data.database          import DatabaseManager

import config
import screens                                                # Automatically imports/registers all screen classes (via __init__.py)

if __name__ == "__main__":
    db = DatabaseManager()                                    # Database
    db.load()

    AppState(db)                                              # State Singleton

    display = MainDisplay(window_size=config.WINDOW_SIZE,     # Main Display
                          framerate=config.FRAMERATE,
                          default_screen="library")

    display.running = True                                    # Start game loop