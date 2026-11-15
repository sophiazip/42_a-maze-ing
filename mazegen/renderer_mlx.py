"""Interactive MiniLibX (MLX) graphical renderer for A-Maze-ing."""

from __future__ import annotations

from dataclasses import replace
import importlib
import random
from typing import Any, Optional, Set, Tuple

from mazegen.config import MazeConfig
from mazegen.generator import Direction, MazeGenerator

_mlx: Any = None
MLX_AVAILABLE = False
try:
    _mlx = importlib.import_module("mlx")
    MLX_AVAILABLE = True
except ImportError:
    pass

WALL_PALETTE: Tuple[Tuple[str, int], ...] = (
    ("Green", 0xFF34A853),
    ("White", 0xFFF1F1F5),
    ("Cyan", 0xFF22D3EE),
    ("Amber", 0xFFFBBF24),
    ("Violet", 0xFFC084FC),
    ("Coral", 0xFFFB7185),
)

PATTERN_PALETTE: Tuple[Tuple[str, int], ...] = (
    ("Forest", 0xFF2E6F40),
    ("Slate", 0xFF475569),
    ("Indigo", 0xFF4F46E5),
    ("Teal", 0xFF0F766E),
)

COLOR_BG = 0xFF050508
COLOR_ENTRY = 0xFF4ADE80
COLOR_EXIT = 0xFFEF4444
COLOR_PATH = 0xFF818CF8
COLOR_TEXT = 0xFFE8E8F0

KEY_1 = 49
KEY_2 = 50
KEY_3 = 51
KEY_4 = 52
KEY_NP_1 = 65457
KEY_NP_2 = 65458
KEY_NP_3 = 65459
KEY_NP_4 = 65460
KEY_C = 99
KEY_P = 112
KEY_Q = 113
KEY_R = 114
KEY_T = 116
KEY_ESC = 65307


class MazeSession:
    """Mutable presentation state for the graphical maze window."""

    def __init__(
        self,
        config: MazeConfig,
        generator: MazeGenerator,
        show_path: bool = True,
    ) -> None:
        """Store configuration, generator, and visual toggles."""
        self.config = config
        self.generator = generator
        self.show_path = show_path
        self.wall_color_index = 0
        self.pattern_color_index = 0

    @property
    def wall_color(self) -> int:
        """Return the current 0xAARRGGBB wall color."""
        return WALL_PALETTE[self.wall_color_index][1]

    @property
    def pattern_color(self) -> int:
        """Return the current 0xAARRGGBB color for '42' cells."""
        return PATTERN_PALETTE[self.pattern_color_index][1]

    def toggle_path(self) -> None:
        """Toggle shortest path visibility."""
        self.show_path = not self.show_path

    def cycle_wall_color(self) -> None:
        """Advance to the next wall color."""
        self.wall_color_index = (
            self.wall_color_index + 1
        ) % len(WALL_PALETTE)

    def cycle_pattern_color(self) -> None:
        """Advance to the next '42' pattern color."""
        self.pattern_color_index = (
            self.pattern_color_index + 1
        ) % len(PATTERN_PALETTE)

    def regenerate(self, seed: Optional[int] = None) -> None:
        """Generate a new maze and update the output file."""
        if seed is None:
            seed = random.randrange(1_000_000)
        self.config = replace(self.config, seed=seed)
        self.generator = MazeGenerator(self.config)
        self.generator.generate()
        self.generator.write_output(self.config.output_file)

    def path_cell_set(self) -> Set[Tuple[int, int]]:
        """Return (row, col) cells on the shortest path when visible."""
        if not self.show_path:
            return set()
        return {(y, x) for x, y in self.generator.shortest_path_coords()}


class MazeWindow:
    """Interactive X11 window powered by MiniLibX."""

    PAD = 16
    BOTTOM_BAR = 44
    MIN_CELL = 8
    MAX_CELL = 36
    MIN_WIN_WIDTH = 440
    WALL_THICKNESS = 2

    def __init__(self, config: MazeConfig, generator: MazeGenerator) -> None:
        """Initialize MLX, allocate image buffer, and render first frame."""
        if not MLX_AVAILABLE or _mlx is None:
            raise RuntimeError(
                "MLX is not installed. Install mlx-2.2-py3-none-any.whl "
                "or run in terminal mode (--display ascii)."
            )

        self.session = MazeSession(config, generator)
        self._closed = False
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
        self.win_h = self.maze_h + 2 * self.PAD + self.BOTTOM_BAR
        self.maze_x = (self.win_w - self.maze_w) // 2
        self.maze_y = self.PAD

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

        self.mlx.mlx_key_hook(self.win, self._on_key_press, None)
        self.mlx.mlx_expose_hook(self.win, self._on_expose, None)
        self.mlx.mlx_hook(self.win, 17, 0, self._on_close, None)
        self.render()

    def _compute_cell_size(self) -> int:
        """Choose a cell pixel size that fits comfortably on screen."""
        _rc, sw, sh = self.mlx.mlx_get_screen_size(self.mlx_ptr)
        avail_w = max(320, int(sw * 0.85) - 2 * self.PAD)
        avail_h = max(240, int(sh * 0.85) - 2 * self.PAD - self.BOTTOM_BAR)
        fit_w = avail_w // self.session.config.width
        fit_h = avail_h // self.session.config.height
        return max(self.MIN_CELL, min(self.MAX_CELL, fit_w, fit_h))

    def _fill_rect(
        self,
        x0: int,
        y0: int,
        width: int,
        height: int,
        color: int,
    ) -> None:
        """Fill a solid rectangle in the 32-bit BGRA image buffer."""
        x_start = max(0, x0)
        y_start = max(0, y0)
        x_end = min(self.win_w, x0 + width)
        y_end = min(self.win_h, y0 + height)
        if x_start >= x_end or y_start >= y_end:
            return
        pixel_bytes = color.to_bytes(4, "little")
        row_bytes = pixel_bytes * (x_end - x_start)
        row_len = len(row_bytes)
        for y in range(y_start, y_end):
            offset = y * self.size_line + x_start * 4
            self.pixels[offset: offset + row_len] = row_bytes

    def _draw_cell_walls(
        self,
        row: int,
        col: int,
        mask: int,
        wall_color: int,
    ) -> None:
        """Draw the closed walls around a single cell."""
        x = self.maze_x + col * self.cell
        y = self.maze_y + row * self.cell
        t = self.WALL_THICKNESS
        s = self.cell
        if mask & int(Direction.NORTH):
            self._fill_rect(x, y, s, t, wall_color)
        if mask & int(Direction.SOUTH):
            self._fill_rect(x, y + s - t, s, t, wall_color)
        if mask & int(Direction.WEST):
            self._fill_rect(x, y, t, s, wall_color)
        if mask & int(Direction.EAST):
            self._fill_rect(x + s - t, y, t, s, wall_color)

    def render(self) -> None:
        """Redraw the maze, markers, shortest path, and footer legend."""
        if self._closed:
            return
        self._fill_rect(0, 0, self.win_w, self.win_h, COLOR_BG)

        gen = self.session.generator
        wall_color = self.session.wall_color
        pattern_color = self.session.pattern_color
        path_cells = self.session.path_cell_set()
        entry_rc = gen.entry_cell
        exit_rc = gen.exit_cell

        marker_pad = max(3, self.cell // 4)
        marker_size = max(2, self.cell - 2 * marker_pad)
        fill_pad = self.WALL_THICKNESS
        fill_size = max(2, self.cell - 2 * fill_pad)

        for r in range(gen.height):
            for c in range(gen.width):
                x = self.maze_x + c * self.cell
                y = self.maze_y + r * self.cell
                rc = (r, c)
                if rc in gen.blocked_cells:
                    self._fill_rect(
                        x + fill_pad,
                        y + fill_pad,
                        fill_size,
                        fill_size,
                        pattern_color,
                    )
                elif rc == entry_rc:
                    self._fill_rect(
                        x + fill_pad,
                        y + fill_pad,
                        fill_size,
                        fill_size,
                        COLOR_ENTRY,
                    )
                elif rc == exit_rc:
                    self._fill_rect(
                        x + fill_pad,
                        y + fill_pad,
                        fill_size,
                        fill_size,
                        COLOR_EXIT,
                    )
                elif rc in path_cells:
                    self._fill_rect(
                        x + marker_pad,
                        y + marker_pad,
                        marker_size,
                        marker_size,
                        COLOR_PATH,
                    )
                self._draw_cell_walls(r, c, gen.grid[r][c], wall_color)

        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win, self.img, 0, 0
        )
        legend = "1: regen    2: path    3: color    4: quit"
        footer_y = self.maze_y + self.maze_h + 16
        self.mlx.mlx_string_put(
            self.mlx_ptr, self.win, self.PAD, footer_y, COLOR_TEXT, legend
        )

    def _on_expose(self, _param: Any) -> int:
        """Handle window expose events."""
        self.render()
        return 0

    def _on_key_press(self, keycode: int, _param: Any) -> int:
        """Handle keyboard shortcuts."""
        if keycode in (KEY_1, KEY_NP_1, KEY_R):
            self.session.regenerate()
            self.render()
        elif keycode in (KEY_2, KEY_NP_2, KEY_P):
            self.session.toggle_path()
            self.render()
        elif keycode in (KEY_3, KEY_NP_3, KEY_C):
            self.session.cycle_wall_color()
            self.render()
        elif keycode == KEY_T:
            self.session.cycle_pattern_color()
            self.render()
        elif keycode in (KEY_4, KEY_NP_4, KEY_Q, KEY_ESC):
            self._on_close(None)
        return 0

    def _on_close(self, _param: Any) -> int:
        """Close the MLX window and exit the event loop cleanly."""
        if not self._closed:
            self._closed = True
            self.mlx.mlx_loop_exit(self.mlx_ptr)
        return 0

    def run(self) -> None:
        """Enter the MLX event loop and release resources on exit."""
        try:
            self.mlx.mlx_loop(self.mlx_ptr)
        finally:
            self.mlx.mlx_destroy_image(self.mlx_ptr, self.img)
            self.mlx.mlx_destroy_window(self.mlx_ptr, self.win)
            self.mlx.mlx_release(self.mlx_ptr)
