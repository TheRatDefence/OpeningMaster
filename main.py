from core.infrastructure import AppState
from core.main_display import MainDisplay
from data.database import DatabaseManager
import screens
# TODO(SP: Wire screen imports): Import LibraryScreen and PracticeScreen here so they self-register via @Screen.register_screen
import config

if __name__ == "__main__":
    db = DatabaseManager()                                  # Database
    # TODO(SP: Load database on startup): Call db.load() here if the save file exists before passing db to AppState

    AppState(db)                                            # State Singleton

    display = MainDisplay(window_size=config.WINDOW_SIZE,   # Main Display
                          framerate=config.FRAMERATE)

    display.running = True                                  # Start game loop