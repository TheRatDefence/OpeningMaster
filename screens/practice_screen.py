import io
import os
from math import sin, pi

import chess
import chess.pgn
import pygame as p
import pygame_gui as pg

from core.infrastructure import Screen, AppState
import config

# ----------| Visual Constants |---------- #
_BOARD_SQUARES      = 8
_HIGHLIGHT_COLOUR   = (255, 255, 0, 120)    # RGBA — selected square
_HOVER_COLOUR       = (100, 180, 255, 100)  # RGBA — drag hover square
_FLASH_COLOUR       = (200, 0, 0)           # RGB  — incorrect move screen flash

# ----------| Layout Constants |---------- #
_BOARD_MARGIN       = 60    # px gap from window edges to board
_PANEL_WIDTH        = 380   # fixed px width of the right panel
_PANEL_MARGIN       = 30    # px gap between board right edge and panel

# ------| Animation / Timing Constants |------ #
_FLASH_DURATION_MS    = 200
_SHAKE_DURATION_MS    = 400
_SHAKE_AMPLITUDE_PX   = 8
_SLIDE_DURATION_MS    = 300
_OPPONENT_DELAY_MS    = 500
_COMPLETE_PAUSE_MS    = 1000


#---------------------------------------------------------------------------------------------------#
#                    AnimationState — owns all timers and animated values                         #
#---------------------------------------------------------------------------------------------------#

class AnimationState:
    """Tracks all in-flight animation state for PracticeScreen."""

    def __init__(self):
        self.flash_timer: float = 0.0

        self.shake_sq: chess.Square | None = None
        self.shake_timer: float = 0.0

        self.slide_from_px: tuple[int, int] | None = None
        self.slide_to_px:   tuple[int, int] | None = None
        self.slide_piece:   str | None = None
        self.slide_sq:      chess.Square | None = None  # destination square
        self.slide_move:    chess.Move | None = None    # move to push on completion
        self.slide_timer:   float = 0.0

        self.opponent_pending: bool = False
        self.opponent_delay:   float = 0.0

        self.complete_timer: float = 0.0

    def reset(self) -> None:
        """Resets all animation state to idle."""
        self.__init__()

    # ----------| Derived Values |---------- #

    @property
    def flash_alpha(self) -> int:
        """Alpha value (0–180) for the red flash overlay."""
        if self.flash_timer <= 0:
            return 0
        return int(180 * self.flash_timer / _FLASH_DURATION_MS)

    @property
    def shake_offset_px(self) -> int:
        """Horizontal offset in pixels for the shake animation."""
        if self.shake_sq is None or self.shake_timer <= 0:
            return 0
        progress = 1.0 - (self.shake_timer / _SHAKE_DURATION_MS)
        return int(sin(progress * 4 * pi) * _SHAKE_AMPLITUDE_PX)

    @property
    def slide_progress(self) -> float:
        """0.0 = at start, 1.0 = at destination."""
        if self.slide_timer <= 0 or self.slide_from_px is None:
            return 1.0
        return 1.0 - (self.slide_timer / _SLIDE_DURATION_MS)

    @property
    def is_sliding(self) -> bool:
        return self.slide_timer > 0 and self.slide_from_px is not None

    @property
    def slide_current_px(self) -> tuple[int, int] | None:
        """Interpolated pixel position of the sliding piece."""
        if not self.is_sliding or self.slide_from_px is None or self.slide_to_px is None:
            return None
        t = self.slide_progress
        fx, fy = self.slide_from_px
        tx, ty = self.slide_to_px
        return int(fx + (tx - fx) * t), int(fy + (ty - fy) * t)

    # ----------| Tick |---------- #

    def tick(self, delta_ms: int) -> list[str]:
        """
        Updates all timers by delta_ms. Returns a list of event strings for any
        timers that just completed: 'slide_complete', 'opponent_due', 'complete_due'.
        """
        events: list[str] = []

        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - delta_ms)

        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - delta_ms)
            if self.shake_timer <= 0:
                self.shake_sq = None

        if self.is_sliding:
            self.slide_timer = max(0.0, self.slide_timer - delta_ms)
            if self.slide_timer <= 0:
                events.append("slide_complete")

        if self.opponent_pending:
            self.opponent_delay = max(0.0, self.opponent_delay - delta_ms)
            if self.opponent_delay <= 0:
                self.opponent_pending = False
                events.append("opponent_due")

        if self.complete_timer > 0:
            self.complete_timer = max(0.0, self.complete_timer - delta_ms)
            if self.complete_timer <= 0:
                events.append("complete_due")

        return events

    # --------| Trigger Helpers |--------- #

    def trigger_flash(self) -> None:
        self.flash_timer = _FLASH_DURATION_MS

    def trigger_shake(self, sq: chess.Square) -> None:
        self.shake_sq = sq
        self.shake_timer = _SHAKE_DURATION_MS

    def trigger_slide(self, from_px: tuple, to_px: tuple, piece: str,
                      dest_sq: chess.Square, move: chess.Move) -> None:
        self.slide_from_px = from_px
        self.slide_to_px   = to_px
        self.slide_piece   = piece
        self.slide_sq      = dest_sq
        self.slide_move    = move
        self.slide_timer   = _SLIDE_DURATION_MS

    def trigger_opponent_delay(self) -> None:
        self.opponent_pending = True
        self.opponent_delay   = _OPPONENT_DELAY_MS

    def trigger_complete_pause(self) -> None:
        self.complete_timer = _COMPLETE_PAUSE_MS


#---------------------------------------------------------------------------------------------------#
#                              BoardRenderer — all drawing logic                                   #
#---------------------------------------------------------------------------------------------------#

class BoardRenderer:
    """Handles all board and piece rendering for PracticeScreen."""

    def __init__(self, square_size: int):
        self.images: dict = self._load_images(square_size)

    # ----------| Image Loading |---------- #

    @staticmethod
    def _load_images(square_size: int) -> dict:
        """Loads and smoothscales all piece PNGs and the board image."""
        piece_files = {
            'P': 'wp', 'N': 'wn', 'B': 'wb', 'R': 'wr', 'Q': 'wq', 'K': 'wk',
            'p': 'bp', 'n': 'bn', 'b': 'bb', 'r': 'br', 'q': 'bq', 'k': 'bk',
        }
        size = (square_size, square_size)
        images = {}
        for symbol, filename in piece_files.items():
            path = os.path.join(config.PIECES_DIR, f"{filename}.png")
            images[symbol] = p.transform.smoothscale(
                p.image.load(path).convert_alpha(), size
            )
        board_px = square_size * _BOARD_SQUARES
        images["board"] = p.transform.smoothscale(
            p.image.load(config.BOARD_IMAGE).convert_alpha(), (board_px, board_px)
        )
        return images

    def reload(self, square_size: int) -> None:
        """Reloads all images at a new square size."""
        self.images = self._load_images(square_size)

    # -------| Coordinate Helpers |-------- #

    @staticmethod
    def visual_row(rank: int, flipped: bool) -> int:
        """
        Converts a chess rank (0=rank1, 7=rank8) to a screen row.
        White: rank 1 at bottom (row 7). Black: rank 8 at bottom (row 7).
        """
        if flipped:
            return rank               # rank 0 (rank1) → top;  rank 7 (rank8) → bottom
        return (_BOARD_SQUARES - 1) - rank  # rank 7 (rank8) → top;  rank 0 (rank1) → bottom

    @staticmethod
    def visual_col(file: int, flipped: bool) -> int:
        """
        Converts a chess file (0=a, 7=h) to a screen column.
        White: a-file on left. Black: h-file on left.
        """
        if flipped:
            return (_BOARD_SQUARES - 1) - file  # h-file → col 0
        return file

    def sq_to_pixel(self, square: chess.Square, board_offset: tuple,
                    square_size: int, flipped: bool) -> tuple[int, int]:
        """Returns the top-left pixel of a square, including board offset."""
        bx, by = board_offset
        col = self.visual_col(chess.square_file(square), flipped)
        row = self.visual_row(chess.square_rank(square), flipped)
        return bx + col * square_size, by + row * square_size

    def square_from_mouse(self, pos: tuple, board_offset: tuple,
                          square_size: int, flipped: bool) -> chess.Square:
        """Converts a mouse pixel position to a chess.Square."""
        bx, by = board_offset
        screen_col = (pos[0] - bx) // square_size
        screen_row = (pos[1] - by) // square_size
        screen_col = max(0, min(_BOARD_SQUARES - 1, screen_col))
        screen_row = max(0, min(_BOARD_SQUARES - 1, screen_row))

        if flipped:
            file = (_BOARD_SQUARES - 1) - screen_col
            rank = screen_row
        else:
            file = screen_col
            rank = (_BOARD_SQUARES - 1) - screen_row

        # DEBUG — remove once coordinate bug is confirmed fixed
        if flipped:
            print(f"[DEBUG flip] mouse={pos} → screen_col={screen_col} screen_row={screen_row} "
                  f"→ file={file} rank={rank} → {chess.square_name(chess.square(file, rank))}")

        return chess.square(file, rank)

    # ----------| Draw Calls |---------- #

    def draw_board(self, surface: p.Surface, board_offset: tuple) -> None:
        """Blits the board image at board_offset."""
        surface.blit(self.images["board"], board_offset)

    def draw_highlights(self, surface: p.Surface, selected_sq: chess.Square | None,
                        hover_sq: chess.Square | None, board_offset: tuple,
                        square_size: int, flipped: bool) -> None:
        """Draws selected-square and drag-hover highlights."""
        for sq, colour in [(selected_sq, _HIGHLIGHT_COLOUR), (hover_sq, _HOVER_COLOUR)]:
            if sq is None:
                continue
            x, y = self.sq_to_pixel(sq, board_offset, square_size, flipped)
            hl = p.Surface((square_size, square_size), p.SRCALPHA)
            hl.fill(colour)
            surface.blit(hl, (x, y))

    @staticmethod
    def build_board_grid(board: chess.Board) -> list[list[str | None]]:
        """
        Converts a chess.Board into an 8x8 grid indexed by [rank][file].
        board_grid[0][0] = a1, board_grid[7][7] = h8.
        Each cell holds the piece symbol (e.g. 'P', 'k') or None if empty.
        """
        board_grid: list[list[str | None]] = [[None] * _BOARD_SQUARES for _ in range(_BOARD_SQUARES)]
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                rank = chess.square_rank(square)
                file = chess.square_file(square)
                board_grid[rank][file] = piece.symbol()
        return board_grid

    def draw_pieces(self, surface: p.Surface, board: chess.Board,
                    drag_from_sq: chess.Square | None,
                    anim: AnimationState,
                    board_offset: tuple, square_size: int, flipped: bool) -> None:
        """Blits all pieces. Skips dragged piece and both ends of any active slide.
        Uses an 8x8 board_grid[rank][file] to look up piece symbols by coordinate."""
        board_grid = self.build_board_grid(board)

        for rank in range(_BOARD_SQUARES):
            for file in range(_BOARD_SQUARES):
                symbol = board_grid[rank][file]
                if symbol is None:
                    continue
                square = chess.square(file, rank)
                if square == drag_from_sq:
                    continue
                if anim.is_sliding and square == anim.slide_sq:
                    continue
                if anim.is_sliding and anim.slide_move is not None and square == anim.slide_move.from_square:
                    continue
                x, y = self.sq_to_pixel(square, board_offset, square_size, flipped)
                if square == anim.shake_sq:
                    x += anim.shake_offset_px
                surface.blit(self.images[symbol], (x, y))

    def draw_drag_piece(self, surface: p.Surface, drag_piece_symbol: str | None,
                        drag_pos: tuple, square_size: int) -> None:
        """Blits the dragged piece centred on the cursor."""
        if drag_piece_symbol is None:
            return
        half = square_size // 2
        surface.blit(self.images[drag_piece_symbol], (drag_pos[0] - half, drag_pos[1] - half))

    def draw_slide_piece(self, surface: p.Surface, anim: AnimationState,
                         square_size: int) -> None:
        """Blits the sliding opponent piece at its interpolated position."""
        if not anim.is_sliding or anim.slide_piece is None:
            return
        pos = anim.slide_current_px
        if pos is None:
            return
        half = square_size // 2
        surface.blit(self.images[anim.slide_piece], (pos[0] - half, pos[1] - half))

    def draw_flash(self, surface: p.Surface, anim: AnimationState,
                   window_size: tuple) -> None:
        """Draws a fading red overlay across the whole window if flash is active."""
        alpha = anim.flash_alpha
        if alpha <= 0:
            return
        flash = p.Surface(window_size, p.SRCALPHA)
        flash.fill((*_FLASH_COLOUR, alpha))
        surface.blit(flash, (0, 0))


# ══════════════════════════════════════════════════════════════════════════════
#  PracticePanel — right-hand UI panel
# ══════════════════════════════════════════════════════════════════════════════

class PracticePanel:
    """
    Owns the right-hand UIPanel and all its child elements.
    Rebuilt whenever the board is resized or the session state changes.
    """

    def __init__(self, ui_manager: pg.UIManager, window_size: tuple):
        self._ui = ui_manager
        self._window_size = window_size

        self._panel:          pg.elements.UIPanel    | None = None
        self._name_label:     pg.elements.UILabel    | None = None
        self._history_box:    pg.elements.UITextBox  | None = None
        self._stuck_btn:      pg.elements.UIButton   | None = None
        self._minus_btn:      pg.elements.UIButton   | None = None
        self._plus_btn:       pg.elements.UIButton   | None = None
        self._side_btns:      list[pg.elements.UIButton] = []
        self._play_again_btn: pg.elements.UIButton   | None = None
        self._return_btn:     pg.elements.UIButton   | None = None

    # ----------| Panel Rect |---------- #

    def _panel_rect(self) -> p.Rect:
        w, h = self._window_size
        x = w - _PANEL_WIDTH - _BOARD_MARGIN
        y = _BOARD_MARGIN
        ph = h - 2 * _BOARD_MARGIN
        return p.Rect(x, y, _PANEL_WIDTH, ph)

    # --------| Percent Helper |--------- #

    def _pct(self, x: float, y: float, w: float, h: float) -> p.Rect:
        assert self._panel is not None
        r = self._panel.get_container().get_rect()
        return p.Rect(r.width * x, r.height * y, r.width * w, r.height * h)

    # -------| Build / Rebuild |-------- #

    def build(self, opening_name: str) -> None:
        """Creates the panel and all its child elements from scratch."""
        self.kill()

        self._panel = pg.elements.UIPanel(
            relative_rect=self._panel_rect(),
            manager=self._ui,
            margins={'left': 12, 'right': 12, 'top': 12, 'bottom': 12},
        )

        self._name_label = pg.elements.UILabel(
            relative_rect=self._pct(0.0, 0.00, 1.0, 0.06),
            text=opening_name,
            manager=self._ui,
            container=self._panel,
        )

        self._history_box = pg.elements.UITextBox(
            relative_rect=self._pct(0.0, 0.07, 1.0, 0.46),
            html_text="",
            manager=self._ui,
            container=self._panel,
        )

        self._stuck_btn = pg.elements.UIButton(
            relative_rect=self._pct(0.05, 0.56, 0.90, 0.06),
            text="Stuck? Show next move",
            manager=self._ui,
            container=self._panel,
        )

        self._minus_btn = pg.elements.UIButton(
            relative_rect=self._pct(0.05, 0.65, 0.38, 0.06),
            text="− Board",
            manager=self._ui,
            container=self._panel,
        )

        self._plus_btn = pg.elements.UIButton(
            relative_rect=self._pct(0.57, 0.65, 0.38, 0.06),
            text="+ Board",
            manager=self._ui,
            container=self._panel,
        )

        labels = ["Play as White", "Play as Black", "Play Both"]
        for i, label in enumerate(labels):
            y = 0.75 + i * 0.07
            btn = pg.elements.UIButton(
                relative_rect=self._pct(0.05, y, 0.90, 0.06),
                text=label,
                manager=self._ui,
                container=self._panel,
            )
            self._side_btns.append(btn)

        # Start with board controls hidden until side is chosen
        self._set_board_controls_visible(False)

    def set_board_active(self, active: bool) -> None:
        """Switches between side-selection UI and active-session UI."""
        self._set_board_controls_visible(active)
        for btn in self._side_btns:
            btn.show() if not active else btn.hide()

    def _set_board_controls_visible(self, visible: bool) -> None:
        for element in [self._stuck_btn, self._minus_btn, self._plus_btn]:
            if element is None:
                continue
            element.show() if visible else element.hide()

    def refresh_history(self, pgn_text: str) -> None:
        """Updates the move history text box."""
        if self._history_box is not None:
            self._history_box.set_text(pgn_text)

    def show_end_buttons(self) -> None:
        """Creates the end-of-session 'Play again?' and 'Return to library' buttons."""
        if self._play_again_btn is not None:
            return
        self._play_again_btn = pg.elements.UIButton(
            relative_rect=self._pct(0.05, 0.75, 0.90, 0.06),
            text="Play again?",
            manager=self._ui,
            container=self._panel,
        )
        self._return_btn = pg.elements.UIButton(
            relative_rect=self._pct(0.05, 0.83, 0.90, 0.06),
            text="Return to library",
            manager=self._ui,
            container=self._panel,
        )

    def kill_end_buttons(self) -> None:
        """Removes the end-of-session buttons."""
        for btn in [self._play_again_btn, self._return_btn]:
            if btn is not None:
                btn.kill()
        self._play_again_btn = None
        self._return_btn     = None

    def kill(self) -> None:
        """Destroys the panel and all its children."""
        if self._panel is not None:
            self._panel.kill()
            self._panel          = None
            self._name_label     = None
            self._history_box    = None
            self._stuck_btn      = None
            self._minus_btn      = None
            self._plus_btn       = None
            self._side_btns      = []
            self._play_again_btn = None
            self._return_btn     = None

    # -----| Button Identity Helpers |------ #

    def is_side_button(self, element) -> bool:
        return element in self._side_btns

    def is_stuck(self, element) -> bool:
        return element is self._stuck_btn

    def is_minus(self, element) -> bool:
        return element is self._minus_btn

    def is_plus(self, element) -> bool:
        return element is self._plus_btn

    def is_play_again(self, element) -> bool:
        return element is self._play_again_btn

    def is_return(self, element) -> bool:
        return element is self._return_btn

    def side_button_text(self, element) -> str | None:
        """Returns the label of a side button, or None if not a side button."""
        if element in self._side_btns:
            return element.text
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  PracticeScreen — orchestrates session logic, input, and rendering
# ══════════════════════════════════════════════════════════════════════════════

@Screen.register_screen("practice")
class PracticeScreen(Screen):

    def __init__(self):
        """Sets up the practice screen with board, panel, and session state."""
        super().__init__()

        opening = self.state.db.get_opening_by_id(self.state.selected_opening_id)
        self._opening = opening
        self._moves   = self._parse_pgn(opening["pgn"]) if opening else []

        self._board      = chess.Board()
        self._board_size = config.BOARD_SIZE_DEFAULT
        self._board_offset: tuple[int, int] = self._calc_board_offset()

        self._renderer = BoardRenderer(self._square_size)
        self._sounds   = self._load_sounds()
        self._anim     = AnimationState()
        self._panel    = PracticePanel(self.local_ui_manager, self.window_size)
        self._panel.build(opening["name"] if opening else "")

        # Drag state
        self._dragging:           bool            = False
        self._drag_piece_symbol:  str | None      = None
        self._drag_from_sq:       chess.Square | None = None
        self._drag_pos:           tuple[int, int] = (0, 0)
        self._selected_sq:        chess.Square | None = None

        # Session state
        self._move_index:      int        = 0
        self._session_results: list[bool] = []
        self._side:            chess.Color | None = None
        self._flipped:         bool       = False
        self._side_selected:   bool       = False
        self._transitioning:   bool       = False
        self._session_ended:   bool       = False

    # ----------| Properties |---------- #

    @property
    def _square_size(self) -> int:
        return self._board_size // _BOARD_SQUARES

    # --------| Setup Helpers |--------- #

    def _calc_board_offset(self) -> tuple[int, int]:
        """Centres the board horizontally in the space left of the panel, vertically in the window."""
        w, h = self.window_size
        available_x = w - _PANEL_WIDTH - _PANEL_MARGIN - _BOARD_MARGIN
        bx = _BOARD_MARGIN + (available_x - self._board_size) // 2
        by = (h - self._board_size) // 2
        return bx, by

    @staticmethod
    def _parse_pgn(pgn: str) -> list:
        """Parses a PGN string and returns an ordered list of chess.Move objects."""
        game = chess.pgn.read_game(io.StringIO(pgn))
        if game is None:
            raise ValueError(f"Failed to parse PGN: {pgn!r}")
        assert game is not None
        return list(game.mainline_moves())

    @staticmethod
    def _load_sounds() -> dict:
        """Loads all sound effects from config.SOUNDS_DIR."""
        files = {
            "move_self":     "move-self.mp3",
            "move_opponent": "move-opponent.mp3",
            "illegal":       "illegal.mp3",
            "capture":       "capture.mp3",
            "game_start":    "game-start.mp3",
            "game_end":      "game-end.mp3",
            "check":         "move-check.mp3",
        }
        return {key: p.mixer.Sound(os.path.join(config.SOUNDS_DIR, fname))
                for key, fname in files.items()}

    def _play(self, key: str) -> None:
        """Plays a sound by key, silently ignoring missing keys."""
        sound = self._sounds.get(key)
        if sound:
            sound.play()

    def _pgn_up_to_index(self) -> str:
        """Returns a PGN-formatted string of all moves played so far."""
        temp = chess.Board()
        parts = []
        for move in self._moves[:self._move_index]:
            if temp.turn == chess.WHITE:
                parts.append(f"{temp.fullmove_number}.")
            parts.append(temp.san(move))
            temp.push(move)
        return " ".join(parts)

    def _is_on_board(self, pos: tuple) -> bool:
        """Returns True if the pixel position is within the board area."""
        bx, by = self._board_offset
        x, y = pos
        return bx <= x < bx + self._board_size and by <= y < by + self._board_size

    # ----------| Rendering |---------- #

    def render(self) -> p.Surface:
        """Draws the full practice screen and returns it."""
        screen = self.local_screen_surface
        screen.fill((30, 30, 30))

        r = self._renderer
        sq = self._square_size
        off = self._board_offset
        fl = self._flipped

        hover_sq = (self._renderer.square_from_mouse(self._drag_pos, off, sq, fl)
                    if self._dragging else None)

        r.draw_board(screen, off)
        r.draw_highlights(screen, self._selected_sq, hover_sq, off, sq, fl)
        r.draw_pieces(screen, self._board, self._drag_from_sq, self._anim, off, sq, fl)
        r.draw_slide_piece(screen, self._anim, sq)
        r.draw_drag_piece(screen, self._drag_piece_symbol, self._drag_pos, sq)
        r.draw_flash(screen, self._anim, self.window_size)

        self.local_ui_manager.draw_ui(screen)
        return screen

    # --------| Input Handling |--------- #

    def handle_event(self, event: p.event.Event) -> None:
        """Routes events to button handler and drag-and-drop logic."""
        super().handle_event(event)

        match event.type:

            case pg.UI_BUTTON_PRESSED:
                self._handle_button(event)

            case p.MOUSEBUTTONDOWN if event.button == 1 and self._side_selected:
                if not self._is_on_board(event.pos) or self._session_ended:
                    return
                sq = self._renderer.square_from_mouse(
                    event.pos, self._board_offset, self._square_size, self._flipped)
                piece = self._board.piece_at(sq)
                if piece and (self._side is None or piece.color == self._board.turn):
                    self._dragging          = True
                    self._drag_from_sq      = sq
                    self._drag_piece_symbol = piece.symbol()
                    self._drag_pos          = event.pos
                    self._selected_sq       = sq

            case p.MOUSEMOTION if self._dragging:
                self._drag_pos = event.pos

            case p.MOUSEBUTTONUP if event.button == 1 and self._dragging:
                dest_sq = self._renderer.square_from_mouse(
                    event.pos, self._board_offset, self._square_size, self._flipped)
                assert self._drag_from_sq is not None
                # Only attempt move if piece actually left its starting square
                if dest_sq != self._drag_from_sq:
                    self.attempt_move(self._drag_from_sq, dest_sq)
                self._dragging          = False
                self._drag_piece_symbol = None
                self._drag_from_sq      = None
                self._selected_sq       = None

    def _handle_button(self, event: p.event.Event) -> None:
        """Resolves button presses and dispatches to the appropriate handler."""
        pressed = event.ui_element

        side_text = self._panel.side_button_text(pressed)
        if side_text is not None:
            self._on_side_selected(side_text)
            return

        if self._panel.is_stuck(pressed):
            if (self._move_index < len(self._moves) and not self._session_ended
                    and not self._anim.is_sliding):
                self._session_results.append(False)
                self.play_opponent_move()
            return

        if self._panel.is_minus(pressed):
            self._resize_board(-1)
        elif self._panel.is_plus(pressed):
            self._resize_board(+1)
        elif self._panel.is_play_again(pressed):
            self._panel.kill_end_buttons()
            self.on_enter()
        elif self._panel.is_return(pressed):
            self._transitioning = True

    def _on_side_selected(self, text: str) -> None:
        """Handles side-selection button press."""
        if text == "Play as White":
            self._side    = chess.WHITE
            self._flipped = False
        elif text == "Play as Black":
            self._side    = chess.BLACK
            self._flipped = True
        else:
            self._side    = None
            self._flipped = False

        self._side_selected = True
        self._panel.set_board_active(True)
        self._play("game_start")

        if self._side is chess.BLACK:
            self._queue_opponent_move()

    def _resize_board(self, direction: int) -> None:
        """Increases or decreases board size by one square increment."""
        step = config.BOARD_SIZE_DEFAULT // _BOARD_SQUARES
        new_size = self._board_size + direction * step
        self._board_size   = max(config.BOARD_SIZE_MIN, min(config.BOARD_SIZE_MAX, new_size))
        self._board_offset = self._calc_board_offset()
        self._renderer.reload(self._square_size)

    # ----------| Move Logic |---------- #

    def attempt_move(self, from_sq: chess.Square, to_sq: chess.Square) -> None:
        """Validates the player's move against the expected move and advances or penalises."""
        if self._move_index >= len(self._moves) or self._anim.is_sliding:
            return

        move     = chess.Move(from_sq, to_sq)
        expected = self._moves[self._move_index]

        if move == expected:
            self._board.push(move)
            self._move_index += 1
            self._session_results.append(True)
            self._panel.refresh_history(self._pgn_up_to_index())

            if self._board.is_check():
                self._play("check")
            elif self._board.is_capture(move):
                self._play("capture")
            else:
                self._play("move_self")

            if self._side is None:
                # Play-both mode: flip board for other side
                self._flipped = not self._flipped
                if self._move_index >= len(self._moves):
                    self.on_session_complete()
            else:
                self._queue_opponent_move()
        else:
            self._anim.trigger_flash()
            self._anim.trigger_shake(from_sq)
            self._play("illegal")
            self._session_results.append(False)

    def _queue_opponent_move(self) -> None:
        """Schedules the opponent's next move after a delay."""
        if self._move_index >= len(self._moves):
            self.on_session_complete()
            return
        self._anim.trigger_opponent_delay()

    def play_opponent_move(self) -> None:
        """
        Starts the slide animation for the opponent's next move.
        The move is pushed to the board only when the slide completes.
        """
        if self._move_index >= len(self._moves):
            self.on_session_complete()
            return

        move  = self._moves[self._move_index]
        piece = self._board.piece_at(move.from_square)
        if piece is None:
            return

        from_px = self._renderer.sq_to_pixel(
            move.from_square, self._board_offset, self._square_size, self._flipped)
        to_px   = self._renderer.sq_to_pixel(
            move.to_square, self._board_offset, self._square_size, self._flipped)

        # Centre positions for smooth interpolation
        half = self._square_size // 2
        from_px = (from_px[0] + half, from_px[1] + half)
        to_px   = (to_px[0]   + half, to_px[1]   + half)

        self._anim.trigger_slide(from_px, to_px, piece.symbol(), move.to_square, move)

    def _finish_opponent_move(self) -> None:
        """Called when the slide animation completes — pushes the move and checks completion."""
        move = self._anim.slide_move
        if move is None:
            return

        self._board.push(move)
        self._move_index += 1
        self._anim.slide_sq   = None
        self._anim.slide_move = None
        self._panel.refresh_history(self._pgn_up_to_index())

        if self._board.is_check():
            self._play("check")
        else:
            self._play("move_opponent")

        if self._move_index >= len(self._moves):
            self.on_session_complete()

    # -------| Session Completion |-------- #

    def on_session_complete(self) -> None:
        """Saves progress, plays end sound, and starts the completion pause."""
        if self._session_ended:
            return
        self._session_ended = True

        memory_points = (sum(self._session_results) / len(self._session_results)
                         if self._session_results else 0.0)

        opening_id   = self._opening["id"] if self._opening else self.state.selected_opening_id
        progress     = self.state.db.get_progress(opening_id) or {}
        review_count = progress.get("review_count", 0) + 1

        self.state.db.upsert_progress(opening_id,
                                      review_count=review_count,
                                      memory_points=memory_points)
        self.state.db.save()
        self._play("game_end")
        self._anim.trigger_complete_pause()

    # ----------| Game Loop |---------- #

    def on_enter(self) -> None:
        """Reloads the selected opening and resets all session state."""
        opening = self.state.db.get_opening_by_id(self.state.selected_opening_id)
        self._opening = opening
        self._moves   = self._parse_pgn(opening["pgn"]) if opening else []

        self._board        = chess.Board()
        self._move_index   = 0
        self._session_results = []
        self._side         = None
        self._flipped      = False
        self._side_selected = False
        self._transitioning = False
        self._session_ended = False

        self._dragging          = False
        self._drag_piece_symbol = None
        self._drag_from_sq      = None
        self._selected_sq       = None

        self._anim.reset()

        self._board_offset = self._calc_board_offset()
        self._renderer.reload(self._square_size)

        self._panel.kill_end_buttons()
        self._panel.kill()
        self._panel.build(opening["name"] if opening else "")
        self._panel.refresh_history("")

    def update(self, delta_ms: int) -> str | None:
        """Ticks animations and handles deferred events. Returns screen transition string or None."""
        super().update(delta_ms)

        events = self._anim.tick(delta_ms)

        for ev in events:
            if ev == "slide_complete":
                self._finish_opponent_move()
            elif ev == "opponent_due":
                self.play_opponent_move()
            elif ev == "complete_due":
                self._panel.show_end_buttons()

        if self._transitioning:
            return "library"
        return None
