"""Interactive terminal ASCII/ANSI renderer for A-Maze-ing."""

from __future__ import annotations

from dataclasses import replace
import random
from typing import List, Optional, Set, Tuple

from mazegen.config import MazeConfig
from mazegen.generator import Direction, MazeGenerator

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_CLEAR = "\033[2J\033[H"

WALL_COLORS: Tuple[Tuple[str, str], ...] = (
    ("White", "\033[97m"),
    ("Green", "\033[92m"),
    ("Cyan", "\033[96m"),
    ("Yellow", "\033[93m"),
    ("Magenta", "\033[95m"),
    ("Blue", "\033[94m"),
)

PATTERN_COLORS: Tuple[Tuple[str, str], ...] = (
    ("Gray", "\033[90m"),
    ("Yellow", "\033[33m"),
    ("Cyan", "\033[36m"),
    ("Magenta", "\033[35m"),
)

COLOR_ENTRY = "\033[95m"
COLOR_EXIT = "\033[91m"
COLOR_PATH = "\033[96m"
BLOCK = "\u2588\u2588"
EMPTY = "  "


def _build_canvas(
    generator: MazeGenerator,
    show_path: bool,
    wall_ansi: str,
    pattern_ansi: str,
) -> List[str]:
    """Build the rendered ANSI lines for the current maze state."""
    rows = generator.height
    cols = generator.width
    canvas_h = 2 * rows + 1
    canvas_w = 2 * cols + 1

    # Store token types: 'W' wall, ' ' empty, '4' pattern, 'E' entry,
    # 'X' exit, 'P' path.
    grid_tokens: List[List[str]] = [
        ["W" for _ in range(canvas_w)] for _ in range(canvas_h)
    ]

    path_set: Set[Tuple[int, int]] = set()
    if show_path:
        for px, py in generator.shortest_path_coords():
            path_set.add((py, px))

    entry_rc = generator.entry_cell
    exit_rc = generator.exit_cell

    for r in range(rows):
        for c in range(cols):
            cr, cc = 2 * r + 1, 2 * c + 1
            cell_rc = (r, c)
            if cell_rc == entry_rc:
                grid_tokens[cr][cc] = "E"
            elif cell_rc == exit_rc:
                grid_tokens[cr][cc] = "X"
            elif cell_rc in generator.blocked_cells:
                grid_tokens[cr][cc] = "4"
            elif cell_rc in path_set:
                grid_tokens[cr][cc] = "P"
            else:
                grid_tokens[cr][cc] = " "

            mask = generator.grid[r][c]
            if not (mask & int(Direction.EAST)) and c + 1 < cols:
                in_path = (
                    show_path
                    and cell_rc in path_set
                    and (r, c + 1) in path_set
                )
                grid_tokens[cr][cc + 1] = "P" if in_path else " "
            if not (mask & int(Direction.SOUTH)) and r + 1 < rows:
                in_path = (
                    show_path
                    and cell_rc in path_set
                    and (r + 1, c) in path_set
                )
                grid_tokens[cr + 1][cc] = "P" if in_path else " "

    lines: List[str] = []
    for row_tokens in grid_tokens:
        parts: List[str] = []
        for token in row_tokens:
            if token == "W":
                parts.append(f"{wall_ansi}{BLOCK}{ANSI_RESET}")
            elif token == "4":
                parts.append(f"{pattern_ansi}{BLOCK}{ANSI_RESET}")
            elif token == "E":
                parts.append(f"{COLOR_ENTRY}{BLOCK}{ANSI_RESET}")
            elif token == "X":
                parts.append(f"{COLOR_EXIT}{BLOCK}{ANSI_RESET}")
            elif token == "P":
                parts.append(f"{COLOR_PATH}{BLOCK}{ANSI_RESET}")
            else:
                parts.append(EMPTY)
        lines.append("".join(parts))
    return lines


def render_ascii(
    generator: MazeGenerator,
    *,
    show_path: bool = False,
    wall_color_idx: int = 0,
    pattern_color_idx: int = 0,
) -> str:
    """Render the maze as an ANSI-colored string.

    Args:
        generator: Generated MazeGenerator instance.
        show_path: Whether to highlight the shortest path.
        wall_color_idx: Index into WALL_COLORS.
        pattern_color_idx: Index into PATTERN_COLORS.

    Returns:
        Multi-line string ready to print to a terminal.
    """
    wall_ansi = WALL_COLORS[wall_color_idx % len(WALL_COLORS)][1]
    pattern_ansi = PATTERN_COLORS[pattern_color_idx % len(PATTERN_COLORS)][1]
    lines = _build_canvas(generator, show_path, wall_ansi, pattern_ansi)
    return "\n".join(lines)


def run_ascii_loop(
    config: MazeConfig,
    generator: MazeGenerator,
    clear_screen: bool = True,
) -> None:
    """Run the interactive terminal menu loop for the maze.

    Args:
        config: Current MazeConfig instance.
        generator: Initially generated MazeGenerator instance.
        clear_screen: Clear terminal before each redraw when True.
    """
    show_path = False
    wall_idx = 0
    pattern_idx = 0
    current_config = config
    current_gen = generator

    while True:
        if clear_screen:
            print(ANSI_CLEAR, end="")
        print(
            render_ascii(
                current_gen,
                show_path=show_path,
                wall_color_idx=wall_idx,
                pattern_color_idx=pattern_idx,
            )
        )
        print("\n=== A-Maze-ing ===")
        print("1. Re-generate a new maze")
        print("2. Show / Hide the shortest path")
        print("3. Rotate the wall colours")
        print("4. Quit")
        try:
            choice = input("Choice? (1-4): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in {"1", "r"}:
            new_seed: Optional[int] = random.randrange(1_000_000)
            current_config = replace(current_config, seed=new_seed)
            current_gen = MazeGenerator(current_config)
            current_gen.generate()
            current_gen.write_output(current_config.output_file)
        elif choice in {"2", "p"}:
            show_path = not show_path
        elif choice in {"3", "c"}:
            wall_idx = (wall_idx + 1) % len(WALL_COLORS)
        elif choice == "t":
            pattern_idx = (pattern_idx + 1) % len(PATTERN_COLORS)
        elif choice in {"4", "q"}:
            break
