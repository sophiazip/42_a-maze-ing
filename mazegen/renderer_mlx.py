"""Interactive MiniLibX (MLX) architectural renderer for A-Maze-ing."""

from __future__ import annotations

import importlib
import time
from typing import Any, List, Tuple

from mazegen.config import MazeConfig
from mazegen.generator import Direction, MazeGenerator
from mazegen.session import MazeSession
from mazegen.sound import ChiptunePlayer

_mlx: Any = None
MLX_AVAILABLE = False
try:
    _mlx = importlib.import_module("mlx")
    MLX_AVAILABLE = True
except ImportError:
    pass

COLOR_BG = 0xFF080A0F
COLOR_HUD = 0xFF111520
COLOR_HUD_BORDER = 0xFF232A3B
COLOR_FLOOR_A = 0xFF0B0E14
COLOR_FLOOR_B = 0xFF0F141D
COLOR_FLOOR_UNCARVED = 0xFF06080C
COLOR_SOLVE_VISITED = 0xFF141D35
COLOR_CURSOR = 0xFFF8FAFC
COLOR_ENTRY_OUTER = 0xFF22C55E
COLOR_ENTRY_INNER = 0xFFBBF7D0
COLOR_EXIT_OUTER = 0xFFEF4444
COLOR_EXIT_INNER = 0xFFFECACA
COLOR_TEXT = 0xFFE2E8F0
COLOR_TEXT_DIM = 0xFF94A3B8
COLOR_TEXT_ACCENT = 0xFF38BDF8

KEYS_REGEN = (49, 65457, 114, 82)   # 1, KP_1, r, R
KEYS_PATH = (50, 65458, 112, 80)    # 2, KP_2, p, P
KEYS_COLOR = (51, 65459, 99, 67)    # 3, KP_3, c, C
KEYS_PATTERN = (116, 84)            # t, T
KEYS_RAINBOW = (98, 66)             # b, B
KEYS_ALGO = (97, 65)                # a, A
KEYS_ENDPOINTS = (101, 69)          # e, E
KEYS_MUTE = (109, 77)               # m, M
KEYS_SPACE = (32,)                  # Space
KEYS_QUIT = (52, 65460, 113, 81, 65307)  # 4, KP_4, q, Q, Esc


def _blend_argb(c1: int, c2: int, t: float) -> int:
    """Linearly interpolate between two 0xAARRGGBB colors."""
    clamped = max(0.0, min(1.0, t))
    r1, g1, b1 = (c1 >> 16) & 0xFF, (c1 >> 8) & 0xFF, c1 & 0xFF
    r2, g2, b2 = (c2 >> 16) & 0xFF, (c2 >> 8) & 0xFF, c2 & 0xFF
    r = int(r1 + (r2 - r1) * clamped)
    g = int(g1 + (g2 - g1) * clamped)
    b = int(b1 + (b2 - b1) * clamped)
    return 0xFF000000 | (r << 16) | (g << 8) | b


class MazeWindow:
    """Interactive X11 window powered by MiniLibX."""

    PAD = 20
    TOP_BAR = 44
    BOTTOM_BAR = 44
    MIN_CELL = 10
    MAX_CELL = 38
    MIN_WIN_WIDTH = 660
    WALL_THICKNESS = 2
    FONT_WIDTH = 11

    def __init__(self, config: MazeConfig, generator: MazeGenerator) -> None:
        """Initialize MLX, allocate image buffer, and render first frame."""
        if not MLX_AVAILABLE or _mlx is None:
            raise RuntimeError(
                "MLX is not installed. Install mlx-2.2-py3-none-any.whl "
                "or run in terminal mode (--display ascii)."
            )

        self.session = MazeSession(config, generator)
        self.sound = ChiptunePlayer()
        self._closed = False
        self._dirty = False
        now = time.monotonic()
        self._last_rainbow_tick = now
        self._last_anim_tick = now
        self._last_sound_tick = now
        self.mlx: Any = _mlx.Mlx()
        self.mlx_ptr: Any = self.mlx.mlx_init()
        if not self.mlx_ptr:
            raise RuntimeError(
                "Could not initialize MLX display (check DISPLAY)."
            )

        self.cell = self._compute_cell_size()
        self.maze_w = config.width * self.cell
        self.maze_h = config.height * self.cell
        self.win_w = max(self.maze_w + 2 * self.PAD, self.MIN_WIN_WIDTH)
        self.win_h = (
            self.maze_h + self.TOP_BAR + self.BOTTOM_BAR + 2 * self.PAD
        )
        self.maze_x = (self.win_w - self.maze_w) // 2
        self.maze_y = self.TOP_BAR + self.PAD

        self.win: Any = self.mlx.mlx_new_window(
            self.mlx_ptr, self.win_w, self.win_h, "A-Maze-ing"
        )
        if not self.win:
            raise RuntimeError("MLX failed to create the application window.")

        self.img: Any = self.mlx.mlx_new_image(
            self.mlx_ptr, self.win_w, self.win_h
        )
        data, bpp, size_line, _fmt = self.mlx.mlx_get_data_addr(self.img)
        if bpp != 32:
            raise RuntimeError(f"Unsupported MLX color depth: {bpp} bits.")
        self.pixels: bytearray = data
        self.size_line: int = size_line

        self.mlx.mlx_do_key_autorepeatoff(self.mlx_ptr)
        self.mlx.mlx_key_hook(self.win, self._on_key_press, self)
        self.mlx.mlx_expose_hook(self.win, self._on_expose, self)
        self.mlx.mlx_hook(self.win, 33, 0, self._on_close, self)
        self.mlx.mlx_loop_hook(self.mlx_ptr, self._on_loop, self)
        self.render()

