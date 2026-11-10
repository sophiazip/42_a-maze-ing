"""Presentation and animation state machine for A-Maze-ing."""

from __future__ import annotations

import colorsys
from dataclasses import replace
import random
from typing import Dict, List, Optional, Set, Tuple

from mazegen.config import ALGORITHMS, MazeConfig
from mazegen.generator import (
    ALL_WALLS,
    Cell,
    MazeGenerator,
    pick_random_endpoints,
)

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

