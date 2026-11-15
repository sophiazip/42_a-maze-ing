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

    def randomize_endpoints(self, seed: Optional[int] = None) -> None:
        """Pick random entry and exit coordinates and regenerate."""
        rng = random.Random(seed)
        entry_pt, exit_pt = pick_random_endpoints(
            self.config.width,
            self.config.height,
            self.generator.blocked_cells,
            rng=rng,
        )
        new_seed = seed if seed is not None else random.randrange(1_000_000)
        self.config = replace(
            self.config, entry=entry_pt, exit=exit_pt, seed=new_seed
        )
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
