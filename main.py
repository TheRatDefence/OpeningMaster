from core.infrastructure    import AppState
from core.main_display      import MainDisplay
from data.database          import DatabaseManager

import config
import screens                                              # Automatically imports/registers all screen classes (via __init__.py)

if __name__ == "__main__":
    db = DatabaseManager()                                  # Database
    # TODO(SP: Load database on startup): Call db.load() here if the save file exists before passing db to AppState

    AppState(db)                                            # State Singleton

    display = MainDisplay(window_size=config.WINDOW_SIZE,   # Main Display
                          framerate=config.FRAMERATE)

    display.running = True                                  # Start game loop