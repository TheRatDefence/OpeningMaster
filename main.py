from Objects.main_display import MainDisplay
from Objects.dashboard_screen import DashboardScreen
#TODO(): Auto initialise Screen classes without having too import
import config

if __name__ == "__main__":
    display = MainDisplay(window_size=config.WINDOW_SIZE,
                          framerate=config.FRAMERATE)

    display.running = True