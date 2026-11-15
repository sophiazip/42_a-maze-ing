"""Interactive MiniLibX (MLX) architectural renderer for A-Maze-ing."""

from __future__ import annotations

import colorsys
from dataclasses import replace
import importlib
import random
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from mazegen.config import MazeConfig
from mazegen.generator import ALL_WALLS, Cell, Direction, MazeGenerator

_mlx: Any = None
MLX_AVAILABLE = False
try:
    _mlx = importlib.import_module("mlx")
    MLX_AVAILABLE = True
except ImportError:
    pass

# (name, wall_color, path_color, path_tint_color)
WALL_PALETTE: Tuple[Tuple[str, int, int, int], ...] = (
    ("Emerald", 0xFF10B981, 0xFF38BDF8, 0xFF0C2D42),
    ("Synth", 0xFFF43F5E, 0xFF22D3EE, 0xFF0E3440),
    ("Amber", 0xFFF59E0B, 0xFF60A5FA, 0xFF13294B),
    ("Nordic", 0xFFE2E8F0, 0xFF818CF8, 0xFF1E224A),
    ("Violet", 0xFFA855F7, 0xFF34D399, 0xFF0D3326),
)

# (name, fill_color, accent_color)
PATTERN_PALETTE: Tuple[Tuple[str, int, int], ...] = (
    ("Slate", 0xFF1E293B, 0xFF334155),
    ("Forest", 0xFF14532D, 0xFF166534),
    ("Indigo", 0xFF312E81, 0xFF4338CA),
    ("Crimson", 0xFF4C0519, 0xFF881337),
)

ALGORITHMS: Tuple[str, ...] = ("backtracker", "kruskal", "prim")

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


def _hsv_to_argb(hue: float, sat: float, val: float) -> int:
    """Convert normalized HSV values to a 0xAARRGGBB integer."""
    r, g, b = colorsys.hsv_to_rgb(hue % 1.0, sat, val)
    return (
        0xFF000000
        | (int(r * 255) << 16)
        | (int(g * 255) << 8)
        | int(b * 255)
    )


class MazeSession:
    """Mutable presentation state for the graphical maze window."""

    def __init__(
        self,
        config: MazeConfig,
        generator: MazeGenerator,
        show_path: bool = True,
    ) -> None:
        """Store configuration, generator, and visual/animation toggles."""
        self.config = config
        self.generator = generator
        self.show_path = show_path
        self.wall_color_index = 0
        self.pattern_color_index = 0
        self.rainbow = False
        self.rainbow_phase = 0.0

        self.anim_phase = "idle"
        self.anim_grid: List[List[int]] = []
        self.carve_idx = 0
        self.carved_cells: Set[Cell] = set()
        self.carve_glow: Dict[Cell, int] = {}
        self.active_cell: Optional[Cell] = None

        self.solve_explored: List[Cell] = []
        self.solve_path: List[Cell] = []
        self.solve_idx = 0
        self.solve_visited: Set[Cell] = set()
        self.solve_glow: Dict[Cell, int] = {}
        self.trace_idx = 0
        self.celebrate_ticks = 0

        if generator.generation_steps:
            self.start_carve_animation()

    @property
    def theme_name(self) -> str:
        """Return the active theme name."""
        if self.rainbow:
            return "Rainbow"
        return WALL_PALETTE[self.wall_color_index][0]

    @property
    def wall_color(self) -> int:
        """Return the current 0xAARRGGBB wall color."""
        if self.rainbow:
            return _hsv_to_argb(self.rainbow_phase, 0.85, 0.96)
        return WALL_PALETTE[self.wall_color_index][1]

    @property
    def path_color(self) -> int:
        """Return the current 0xAARRGGBB path ribbon color."""
        if self.rainbow:
            return _hsv_to_argb(self.rainbow_phase + 0.55, 0.80, 0.96)
        return WALL_PALETTE[self.wall_color_index][2]

    @property
    def path_tint(self) -> int:
        """Return the current 0xAARRGGBB path cell tint color."""
        if self.rainbow:
            return _hsv_to_argb(self.rainbow_phase + 0.55, 0.75, 0.24)
        return WALL_PALETTE[self.wall_color_index][3]

    @property
    def pattern_color(self) -> int:
        """Return the current 0xAARRGGBB fill color for '42' cells."""
        if self.rainbow:
            return _hsv_to_argb(self.rainbow_phase + 0.33, 0.78, 0.42)
        return PATTERN_PALETTE[self.pattern_color_index][1]

    @property
    def pattern_accent(self) -> int:
        """Return the current 0xAARRGGBB inner bevel color for '42' cells."""
        if self.rainbow:
            return _hsv_to_argb(self.rainbow_phase + 0.33, 0.80, 0.72)
        return PATTERN_PALETTE[self.pattern_color_index][2]

    def toggle_path(self) -> None:
        """Toggle shortest path visibility and animate solver on reveal."""
        self.show_path = not self.show_path
        if self.show_path and self.anim_phase == "idle":
            self.start_solve_animation()
        elif not self.show_path and self.anim_phase in (
            "solving", "tracing", "celebrate"
        ):
            self.anim_phase = "idle"
            self.active_cell = None
            self.solve_visited.clear()
            self.solve_glow.clear()

    def toggle_rainbow(self) -> None:
        """Toggle animated rainbow color cycling."""
        self.rainbow = not self.rainbow

    def advance_rainbow(self, delta: float = 0.02) -> None:
        """Advance the rainbow hue phase."""
        self.rainbow_phase = (self.rainbow_phase + delta) % 1.0

    def cycle_wall_color(self) -> None:
        """Advance to the next color theme."""
        self.rainbow = False
        self.wall_color_index = (
            self.wall_color_index + 1
        ) % len(WALL_PALETTE)

    def cycle_pattern_color(self) -> None:
        """Advance to the next '42' pattern color."""
        self.rainbow = False
        self.pattern_color_index = (
            self.pattern_color_index + 1
        ) % len(PATTERN_PALETTE)

    def cycle_algorithm(self) -> None:
        """Switch to the next generation algorithm and regenerate."""
        cur_idx = ALGORITHMS.index(self.config.algorithm)
        next_algo = ALGORITHMS[(cur_idx + 1) % len(ALGORITHMS)]
        self.config = replace(self.config, algorithm=next_algo)
        self.generator = MazeGenerator(self.config)
        self.generator.generate(record_steps=True)
        self.generator.write_output(self.config.output_file)
        self.start_carve_animation()

    def regenerate(self, seed: Optional[int] = None) -> None:
        """Generate a new maze and update the output file."""
        if seed is None:
            seed = random.randrange(1_000_000)
        self.config = replace(self.config, seed=seed)
        self.generator = MazeGenerator(self.config)
        self.generator.generate(record_steps=True)
        self.generator.write_output(self.config.output_file)
        self.start_carve_animation()

    @property
    def is_animating(self) -> bool:
        """Return True while generation or solver animation is playing."""
        return self.anim_phase != "idle"

    @property
    def phase_label(self) -> str:
        """Return short HUD label for the current animation phase."""
        labels = {
            "carving": "CARVING",
            "solving": "SOLVING",
            "tracing": "LOCKING",
            "celebrate": "SOLVED!",
        }
        return labels.get(self.anim_phase, "")

    @property
    def display_grid(self) -> List[List[int]]:
        """Return the grid to draw (animated carving buffer or final)."""
        if self.anim_phase == "carving" and self.anim_grid:
            return self.anim_grid
        return self.generator.grid

    def start_carve_animation(self) -> None:
        """Reset playback to animate maze carving from a closed grid."""
        gen = self.generator
        self.anim_grid = [
            [ALL_WALLS for _ in range(gen.width)] for _ in range(gen.height)
        ]
        self.carve_idx = 0
        self.carved_cells = {gen.entry_cell}
        self.carve_glow = {gen.entry_cell: 8}
        self.active_cell = gen.entry_cell
        self.solve_explored = []
        self.solve_path = []
        self.solve_idx = 0
        self.solve_visited.clear()
        self.solve_glow.clear()
        self.trace_idx = 0
        self.celebrate_ticks = 0
        if gen.generation_steps:
            self.anim_phase = "carving"
        elif self.show_path:
            self.start_solve_animation()
        else:
            self.anim_phase = "idle"
            self.active_cell = None

    def start_solve_animation(self) -> None:
        """Prepare BFS wavefront and shortest-path lock-in playback."""
        explored, path = self.generator.solve_with_trace()
        self.solve_explored = explored
        self.solve_path = path
        self.solve_idx = 0
        self.solve_visited.clear()
        self.solve_glow.clear()
        self.trace_idx = 0
        self.celebrate_ticks = 0
        self.active_cell = self.generator.entry_cell
        self.anim_phase = "solving"

    def replay_or_skip(self) -> None:
        """Skip active animation to completion, or replay from start."""
        if self.is_animating:
            self.skip_animation()
        elif self.generator.generation_steps:
            self.start_carve_animation()
        elif self.show_path:
            self.start_solve_animation()

    def skip_animation(self) -> None:
        """Immediately finish any running animation."""
        self.anim_phase = "idle"
        self.anim_grid = []
        self.carve_glow.clear()
        self.solve_visited.clear()
        self.solve_glow.clear()
        self.active_cell = None

    def _decay_glow(self, glow_map: Dict[Cell, int]) -> None:
        """Decrement glow counters and prune faded cells."""
        expired: List[Cell] = []
        for cell, val in glow_map.items():
            if val <= 1:
                expired.append(cell)
            else:
                glow_map[cell] = val - 1
        for cell in expired:
            del glow_map[cell]

    def step_animation(self) -> bool:
        """Advance active animation by one tick; return True if changed."""
        if self.anim_phase == "idle":
            return False

        self._decay_glow(self.carve_glow)
        self._decay_glow(self.solve_glow)

        if self.anim_phase == "carving":
            steps = self.generator.generation_steps
            batch = max(1, len(steps) // 140)
            end_idx = min(len(steps), self.carve_idx + batch)
            for idx in range(self.carve_idx, end_idx):
                step = steps[idx]
                if step.cell_b is not None and step.direction is not None:
                    r1, c1 = step.cell_a
                    r2, c2 = step.cell_b
                    self.anim_grid[r1][c1] &= ~int(step.direction)
                    self.anim_grid[r2][c2] &= ~int(step.direction.opposite)
                    self.carved_cells.add(step.cell_a)
                    self.carved_cells.add(step.cell_b)
                    self.carve_glow[step.cell_b] = 8
                self.carve_glow[step.active] = 8
                self.active_cell = step.active
            self.carve_idx = end_idx
            if self.carve_idx >= len(steps):
                if self.show_path:
                    self.start_solve_animation()
                else:
                    self.skip_animation()
            return True

        if self.anim_phase == "solving":
            batch = max(1, len(self.solve_explored) // 90)
            end_idx = min(len(self.solve_explored), self.solve_idx + batch)
            for idx in range(self.solve_idx, end_idx):
                cell = self.solve_explored[idx]
                self.solve_visited.add(cell)
                self.solve_glow[cell] = 7
                self.active_cell = cell
            self.solve_idx = end_idx
            if self.solve_idx >= len(self.solve_explored):
                self.anim_phase = "tracing"
                self.trace_idx = 1 if self.solve_path else 0
                self.active_cell = (
                    self.solve_path[0] if self.solve_path else None
                )
            return True

        if self.anim_phase == "tracing":
            batch = max(1, len(self.solve_path) // 35)
            self.trace_idx = min(len(self.solve_path), self.trace_idx + batch)
            if self.trace_idx > 0:
                self.active_cell = self.solve_path[self.trace_idx - 1]
            if self.trace_idx >= len(self.solve_path):
                self.anim_phase = "celebrate"
                self.celebrate_ticks = 12
                self.active_cell = self.generator.exit_cell
            return True

        if self.anim_phase == "celebrate":
            self.celebrate_ticks -= 1
            if self.celebrate_ticks <= 0:
                self.skip_animation()
            return True

        return False

    def path_cell_set(self) -> Set[Tuple[int, int]]:
        """Return (row, col) cells on the visible portion of shortest path."""
        if not self.show_path or self.anim_phase in ("carving", "solving"):
            return set()
        if self.anim_phase == "tracing":
            return set(self.solve_path[:self.trace_idx])
        return {(y, x) for x, y in self.generator.shortest_path_coords()}

    def path_coords_ordered(self) -> List[Tuple[int, int]]:
        """Return ordered (row, col) cells along the visible shortest path."""
        if not self.show_path or self.anim_phase in ("carving", "solving"):
            return []
        if self.anim_phase == "tracing":
            return list(self.solve_path[:self.trace_idx])
        return [(y, x) for x, y in self.generator.shortest_path_coords()]


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
        self._closed = False
        self._dirty = False
        now = time.monotonic()
        self._last_rainbow_tick = now
        self._last_anim_tick = now
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

    def _compute_cell_size(self) -> int:
        """Choose a cell pixel size that fits comfortably on screen."""
        _rc, sw, sh = self.mlx.mlx_get_screen_size(self.mlx_ptr)
        avail_w = max(320, int(sw * 0.85) - 2 * self.PAD)
        avail_h = max(
            240,
            int(sh * 0.85) - self.TOP_BAR - self.BOTTOM_BAR - 2 * self.PAD,
        )
        fit_w = avail_w // self.session.config.width
        fit_h = avail_h // self.session.config.height
        return max(self.MIN_CELL, min(self.MAX_CELL, fit_w, fit_h))

    def _fit(self, text: str, max_px: int) -> str:
        """Truncate text so it never overflows max_px."""
        limit = max(1, max_px // self.FONT_WIDTH)
        if len(text) <= limit:
            return text
        if limit <= 3:
            return text[:limit]
        return text[:limit - 3] + "..."

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

    def _draw_path_ribbon(
        self,
        ordered: List[Tuple[int, int]],
        path_color: int,
    ) -> None:
        """Draw a continuous ribbon connecting cells on the shortest path."""
        if len(ordered) < 2:
            return
        ribbon = max(4, self.cell // 3)
        half = ribbon // 2
        for idx in range(len(ordered) - 1):
            r1, c1 = ordered[idx]
            r2, c2 = ordered[idx + 1]
            cx1 = self.maze_x + c1 * self.cell + self.cell // 2
            cy1 = self.maze_y + r1 * self.cell + self.cell // 2
            cx2 = self.maze_x + c2 * self.cell + self.cell // 2
            cy2 = self.maze_y + r2 * self.cell + self.cell // 2
            x0 = min(cx1, cx2) - half
            y0 = min(cy1, cy2) - half
            w = abs(cx2 - cx1) + ribbon
            h = abs(cy2 - cy1) + ribbon
            self._fill_rect(x0, y0, w, h, path_color)

    def _draw_beacon(
        self,
        row: int,
        col: int,
        outer_color: int,
        inner_color: int,
    ) -> None:
        """Draw a concentric square beacon for entry or exit."""
        x = self.maze_x + col * self.cell
        y = self.maze_y + row * self.cell
        outer_pad = max(3, self.cell // 6)
        inner_pad = max(5, self.cell // 3)
        self._fill_rect(
            x + outer_pad,
            y + outer_pad,
            self.cell - 2 * outer_pad,
            self.cell - 2 * outer_pad,
            outer_color,
        )
        self._fill_rect(
            x + inner_pad,
            y + inner_pad,
            max(2, self.cell - 2 * inner_pad),
            max(2, self.cell - 2 * inner_pad),
            inner_color,
        )

    def _draw_hud_bars(self) -> None:
        """Draw top status bar and bottom control bar chrome."""
        self._fill_rect(0, 0, self.win_w, self.TOP_BAR, COLOR_HUD)
        self._fill_rect(0, self.TOP_BAR - 1, self.win_w, 1, COLOR_HUD_BORDER)

        footer_y = self.win_h - self.BOTTOM_BAR
        self._fill_rect(0, footer_y, self.win_w, self.BOTTOM_BAR, COLOR_HUD)
        self._fill_rect(0, footer_y, self.win_w, 1, COLOR_HUD_BORDER)

        swatch_size = 16
        swatch_x = self.win_w - self.PAD - swatch_size
        swatch_y = footer_y + (self.BOTTOM_BAR - swatch_size) // 2
        self._fill_rect(
            swatch_x - 1,
            swatch_y - 1,
            swatch_size + 2,
            swatch_size + 2,
            COLOR_HUD_BORDER,
        )
        self._fill_rect(
            swatch_x, swatch_y, swatch_size, swatch_size,
            self.session.wall_color,
        )

    def render(self) -> None:
        """Redraw the HUD, floor checkerboard, walls, path, and markers."""
        if self._closed:
            return
        self._fill_rect(0, 0, self.win_w, self.win_h, COLOR_BG)
        self._draw_hud_bars()

        gen = self.session.generator
        grid = self.session.display_grid
        wall_color = self.session.wall_color
        path_set = self.session.path_cell_set()
        ordered_path = self.session.path_coords_ordered()
        entry_rc = gen.entry_cell
        exit_rc = gen.exit_cell
        carving = self.session.anim_phase == "carving"
        celebrate_flash = (
            self.session.anim_phase == "celebrate"
            and self.session.celebrate_ticks % 2 == 0
        )

        for r in range(gen.height):
            for c in range(gen.width):
                x = self.maze_x + c * self.cell
                y = self.maze_y + r * self.cell
                rc = (r, c)
                if rc in gen.blocked_cells:
                    self._fill_rect(
                        x, y, self.cell, self.cell, self.session.pattern_color
                    )
                    pad = max(3, self.cell // 4)
                    self._fill_rect(
                        x + pad,
                        y + pad,
                        max(2, self.cell - 2 * pad),
                        max(2, self.cell - 2 * pad),
                        self.session.pattern_accent,
                    )
                elif rc in path_set:
                    tint = self.session.path_tint
                    if celebrate_flash:
                        tint = _blend_argb(tint, self.session.path_color, 0.45)
                    self._fill_rect(x, y, self.cell, self.cell, tint)
                else:
                    floor = (
                        COLOR_FLOOR_A if (r + c) % 2 == 0 else COLOR_FLOOR_B
                    )
                    if carving and rc not in self.session.carved_cells:
                        floor = COLOR_FLOOR_UNCARVED
                    elif rc in self.session.solve_glow:
                        floor = _blend_argb(
                            COLOR_SOLVE_VISITED,
                            self.session.path_color,
                            self.session.solve_glow[rc] / 7.0,
                        )
                    elif rc in self.session.solve_visited:
                        floor = COLOR_SOLVE_VISITED
                    if rc in self.session.carve_glow:
                        floor = _blend_argb(
                            floor,
                            wall_color,
                            self.session.carve_glow[rc] / 10.0,
                        )
                    self._fill_rect(x, y, self.cell, self.cell, floor)

        ribbon_color = (
            _blend_argb(self.session.path_color, COLOR_CURSOR, 0.55)
            if celebrate_flash
            else self.session.path_color
        )
        self._draw_path_ribbon(ordered_path, ribbon_color)
        self._draw_beacon(
            entry_rc[0], entry_rc[1], COLOR_ENTRY_OUTER, COLOR_ENTRY_INNER
        )
        self._draw_beacon(
            exit_rc[0], exit_rc[1], COLOR_EXIT_OUTER, COLOR_EXIT_INNER
        )
        if (
            self.session.active_cell is not None
            and self.session.anim_phase in ("carving", "solving", "tracing")
        ):
            ar, ac = self.session.active_cell
            self._draw_beacon(ar, ac, self.session.path_color, COLOR_CURSOR)

        for r in range(gen.height):
            for c in range(gen.width):
                self._draw_cell_walls(r, c, grid[r][c], wall_color)

        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win, self.img, 0, 0
        )

        cfg = self.session.config
        mode = "PERFECT" if cfg.perfect else "BRAIDED"
        self.mlx.mlx_string_put(
            self.mlx_ptr, self.win, self.PAD, 13,
            COLOR_TEXT_ACCENT, "A-MAZE-ING",
        )
        phase = self.session.phase_label
        meta_raw = (
            f"{phase} | {cfg.width}x{cfg.height} | {cfg.algorithm} | {mode}"
            if phase
            else f"{cfg.width}x{cfg.height} | {cfg.algorithm} | {mode}"
        )
        meta = self._fit(
            meta_raw,
            self.win_w - 2 * self.PAD - 130,
        )
        meta_x = self.win_w - self.PAD - len(meta) * self.FONT_WIDTH
        self.mlx.mlx_string_put(
            self.mlx_ptr, self.win, meta_x, 13, COLOR_TEXT_DIM, meta
        )

        footer_y = self.win_h - self.BOTTOM_BAR + 13
        space_lbl = "Spc:Skip" if self.session.is_animating else "Spc:Play"
        controls = self._fit(
            f"1:Regen 2:Path 3:Theme T:42 B:Rainbow A:Algo {space_lbl} 4:Quit",
            self.win_w - 2 * self.PAD - 36,
        )
        self.mlx.mlx_string_put(
            self.mlx_ptr, self.win, self.PAD, footer_y, COLOR_TEXT, controls
        )

        self.mlx.mlx_do_sync(self.mlx_ptr)
        self._dirty = False

    def _on_loop(self, _param: Any) -> None:
        """Redraw pending state, step animations, and animate rainbow mode."""
        if self._closed:
            return
        now = time.monotonic()
        if self.session.is_animating and now - self._last_anim_tick >= 0.016:
            self._last_anim_tick = now
            if self.session.step_animation():
                self._dirty = True
        if self.session.rainbow and now - self._last_rainbow_tick >= 0.05:
            self._last_rainbow_tick = now
            self.session.advance_rainbow(0.015)
            self._dirty = True
        if self._dirty:
            self.render()

    def _on_expose(self, _param: Any) -> None:
        """Request a redraw when the window is exposed."""
        self._dirty = True

    def _on_key_press(self, keycode: int, _param: Any) -> None:
        """Handle keyboard shortcuts."""
        if self._closed:
            return
        if keycode in KEYS_REGEN:
            self.session.regenerate()
            self._dirty = True
        elif keycode in KEYS_PATH:
            self.session.toggle_path()
            self._dirty = True
        elif keycode in KEYS_COLOR:
            self.session.cycle_wall_color()
            self._dirty = True
        elif keycode in KEYS_PATTERN:
            self.session.cycle_pattern_color()
            self._dirty = True
        elif keycode in KEYS_RAINBOW:
            self.session.toggle_rainbow()
            self._last_rainbow_tick = time.monotonic()
            self._dirty = True
        elif keycode in KEYS_ALGO:
            self.session.cycle_algorithm()
            self._last_anim_tick = time.monotonic()
            self._dirty = True
        elif keycode in KEYS_SPACE:
            self.session.replay_or_skip()
            self._last_anim_tick = time.monotonic()
            self._dirty = True
        elif keycode in KEYS_QUIT:
            self._on_close(self)

    def _on_close(self, _param: Any) -> None:
        """Exit the MLX event loop cleanly."""
        if not self._closed:
            self.mlx.mlx_loop_exit(self.mlx_ptr)

    def run(self) -> None:
        """Enter the MLX event loop and release resources on exit."""
        try:
            self.mlx.mlx_loop(self.mlx_ptr)
        finally:
            self._closed = True
            self.mlx.mlx_destroy_image(self.mlx_ptr, self.img)
            self.mlx.mlx_destroy_window(self.mlx_ptr, self.win)
            self.mlx.mlx_release(self.mlx_ptr)
