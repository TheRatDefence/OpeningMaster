import os

WINDOW_SIZE = (640, 640)    # The size of the window in pixels
FRAMERATE = 165             # The framerate in frames per second

# Paths
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "data")
DB_PATH     = os.path.join(DATA_DIR, "save.db.enc")

ASSETS_DIR  = os.path.join(BASE_DIR, "Assets", "chess.com-boards-and-pieces-master")
BOARDS_DIR  = os.path.join(ASSETS_DIR, "boards")
PIECES_DIR  = os.path.join(ASSETS_DIR, "pieces")

# Board / piece style — change to any folder name inside PIECES_DIR
PIECE_STYLE = "classic"
BOARD_IMAGE = os.path.join(BOARDS_DIR, "brown.png")

SQUARE_SIZE = WINDOW_SIZE[0] // 8  # 80px