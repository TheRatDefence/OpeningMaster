import os

WINDOW_SIZE = (1920, 1080)  # The size of the window in pixels
FRAMERATE = 165             # The framerate in frames per second

# Board sizing — SQUARE_SIZE is dynamic (board_size // 8) on PracticeScreen
BOARD_SIZE_DEFAULT = 640
BOARD_SIZE_MIN     = 320
BOARD_SIZE_MAX     = 960

# Paths
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "data")
DB_PATH     = os.path.join(DATA_DIR, "save.db.enc")

ASSETS_DIR  = os.path.join(BASE_DIR, "Assets")
PIECES_DIR  = os.path.join(ASSETS_DIR, "neo-pieces")       # TODO: Document removal of PIECE_STYLE switcher in vault
BOARD_IMAGE = os.path.join(ASSETS_DIR, "green-board.png")
SOUNDS_DIR  = os.path.join(ASSETS_DIR, "Sounds")
