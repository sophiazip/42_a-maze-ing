"""Interactive terminal box-drawing ANSI renderer for A-Maze-ing."""

from __future__ import annotations

from dataclasses import replace
import random
import time
from typing import Dict, List, Optional, Set, Tuple

from mazegen.config import MazeConfig
from mazegen.generator import ALL_WALLS, Direction, MazeGenerator

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_CLEAR = "\033[2J\033[H"

# (name, wall_ansi, path_ansi)
WALL_THEMES: Tuple[Tuple[str, str, str], ...] = (
    ("Emerald", "\033[92m", "\033[96m"),
    ("Nordic", "\033[97m", "\033[94m"),
    ("Amber", "\033[93m", "\033[96m"),
    ("Synth", "\033[95m", "\033[92m"),
    ("Ocean", "\033[96m", "\033[93m"),
    ("Crimson", "\033[91m", "\033[97m"),
)

PATTERN_COLORS: Tuple[Tuple[str, str], ...] = (
    ("Slate", "\033[90m"),
    ("Teal", "\033[36m"),
    ("Gold", "\033[33m"),
    ("Violet", "\033[35m"),
)

ALGORITHMS: Tuple[str, ...] = ("backtracker", "kruskal", "prim")

COLOR_ENTRY = "\033[92;1m"
COLOR_EXIT = "\033[91;1m"
COLOR_HUD = "\033[97;1m"

# Vertex bitmask: 1=Up, 2=Right, 4=Down, 8=Left
JUNCTION_GLYPHS: Dict[int, str] = {
    0: " ",
    1: "\u2579",   # ╹
    2: "\u257a",   # ╺
    3: "\u2517",   # ┗
    4: "\u257b",   # ╻
    5: "\u2503",   # ┃
    6: "\u250f",   # ┏
    7: "\u2523",   # ┣
    8: "\u2578",   # ╸
    9: "\u251b",   # ┛
    10: "\u2501",  # ━
    11: "\u253b",  # ┻
    12: "\u2513",  # ┓
    13: "\u252b",  # ┫
    14: "\u2533",  # ┳
    15: "\u254b",  # ╋
}

H_WALL = "\u2501\u2501\u2501"
V_WALL = "\u2503"
PATTERN_FILL = "\u2593\u2593\u2593"
ENTRY_GLYPH = " \u25c6 "
EXIT_GLYPH = " \u2605 "
PATH_DOT = " \u2022 "
PATH_BRIDGE_H = "\u2022"
PATH_BRIDGE_V = " \u2022 "


def _has_horizontal_wall(gen: MazeGenerator, vr: int, col: int) -> bool:
    """Return True if a horizontal wall exists above cell (vr, col)."""
    if vr == 0:
        return bool(gen.grid[0][col] & int(Direction.NORTH))
    if vr == gen.height:
        return bool(gen.grid[gen.height - 1][col] & int(Direction.SOUTH))
    return bool(gen.grid[vr][col] & int(Direction.NORTH))


def _has_vertical_wall(gen: MazeGenerator, row: int, vc: int) -> bool:
    """Return True if a vertical wall exists left of cell (row, vc)."""
    if vc == 0:
        return bool(gen.grid[row][0] & int(Direction.WEST))
    if vc == gen.width:
        return bool(gen.grid[row][gen.width - 1] & int(Direction.EAST))
    return bool(gen.grid[row][vc] & int(Direction.WEST))


def _vertex_glyph(gen: MazeGenerator, vr: int, vc: int) -> str:
    """Compute the exact heavy box-drawing junction at vertex (vr, vc)."""
    mask = 0
    if vr > 0 and _has_vertical_wall(gen, vr - 1, vc):
        mask |= 1
    if vc < gen.width and _has_horizontal_wall(gen, vr, vc):
        mask |= 2
    if vr < gen.height and _has_vertical_wall(gen, vr, vc):
        mask |= 4
    if vc > 0 and _has_horizontal_wall(gen, vr, vc - 1):
        mask |= 8
    return JUNCTION_GLYPHS[mask]


def _render_horizontal_border(
    gen: MazeGenerator,
    vr: int,
    wall_ansi: str,
    path_ansi: str,
    path_set: Set[Tuple[int, int]],
    show_path: bool,
) -> str:
    """Render vertex row vr and horizontal wall segments between cells."""
    parts: List[str] = []
    for vc in range(gen.width + 1):
        parts.append(f"{wall_ansi}{_vertex_glyph(gen, vr, vc)}{ANSI_RESET}")
        if vc < gen.width:
            if _has_horizontal_wall(gen, vr, vc):
                parts.append(f"{wall_ansi}{H_WALL}{ANSI_RESET}")
            elif (
                show_path
                and 0 < vr < gen.height
                and (vr - 1, vc) in path_set
                and (vr, vc) in path_set
            ):
                parts.append(f"{path_ansi}{PATH_BRIDGE_V}{ANSI_RESET}")
            else:
                parts.append("   ")
    return "".join(parts)


def _render_cell_row(
    gen: MazeGenerator,
    row: int,
    wall_ansi: str,
    path_ansi: str,
    pattern_ansi: str,
    path_set: Set[Tuple[int, int]],
    show_path: bool,
) -> str:
    """Render cell row with vertical walls, entry/exit, '42', and path."""
    parts: List[str] = []
    entry_rc = gen.entry_cell
    exit_rc = gen.exit_cell

    for vc in range(gen.width + 1):
        if _has_vertical_wall(gen, row, vc):
            parts.append(f"{wall_ansi}{V_WALL}{ANSI_RESET}")
        elif (
            show_path
            and 0 < vc < gen.width
            and (row, vc - 1) in path_set
            and (row, vc) in path_set
        ):
            parts.append(f"{path_ansi}{PATH_BRIDGE_H}{ANSI_RESET}")
        else:
            parts.append(" ")

        if vc < gen.width:
            rc = (row, vc)
            if rc == entry_rc:
                parts.append(f"{COLOR_ENTRY}{ENTRY_GLYPH}{ANSI_RESET}")
            elif rc == exit_rc:
                parts.append(f"{COLOR_EXIT}{EXIT_GLYPH}{ANSI_RESET}")
            elif rc in gen.blocked_cells:
                parts.append(f"{pattern_ansi}{PATTERN_FILL}{ANSI_RESET}")
            elif show_path and rc in path_set:
                parts.append(f"{path_ansi}{PATH_DOT}{ANSI_RESET}")
            else:
                parts.append("   ")
    return "".join(parts)


def render_ascii(
    generator: MazeGenerator,
    *,
    show_path: bool = False,
    wall_color_idx: int = 0,
    pattern_color_idx: int = 0,
) -> str:
    """Render the maze using seamless Unicode box-drawing walls.

    Args:
        generator: Generated MazeGenerator instance.
        show_path: Whether to highlight the shortest path.
        wall_color_idx: Index into WALL_THEMES.
        pattern_color_idx: Index into PATTERN_COLORS.

    Returns:
        Multi-line ANSI string ready to print to a terminal.
    """
    _name, wall_ansi, path_ansi = WALL_THEMES[
        wall_color_idx % len(WALL_THEMES)
    ]
    pattern_ansi = PATTERN_COLORS[
        pattern_color_idx % len(PATTERN_COLORS)
    ][1]

    path_set: Set[Tuple[int, int]] = set()
    if show_path:
        path_set = {(y, x) for x, y in generator.shortest_path_coords()}

    lines: List[str] = []
    for r in range(generator.height):
        lines.append(
            _render_horizontal_border(
                generator, r, wall_ansi, path_ansi, path_set, show_path
            )
        )
        lines.append(
            _render_cell_row(
                generator,
                r,
                wall_ansi,
                path_ansi,
                pattern_ansi,
                path_set,
                show_path,
            )
        )
    lines.append(
        _render_horizontal_border(
            generator,
            generator.height,
            wall_ansi,
            path_ansi,
            path_set,
            show_path,
        )
    )
    return "\n".join(lines)


def run_ascii_loop(
    config: MazeConfig,
    generator: MazeGenerator,
    clear_screen: bool = True,
) -> None:
    """Run the interactive terminal HUD and command loop."""
    show_path = False
    wall_idx = 0
    pattern_idx = 0
    rainbow = False
    current_config = config
    current_gen = generator

    while True:
        if clear_screen:
            print(ANSI_CLEAR, end="")

        if rainbow:
            wall_idx = (wall_idx + 1) % len(WALL_THEMES)
            pattern_idx = (pattern_idx + 1) % len(PATTERN_COLORS)

        theme_name, wall_ansi, _ = WALL_THEMES[wall_idx % len(WALL_THEMES)]
        mode_label = "PERFECT" if current_config.perfect else "BRAIDED"
        steps = len(current_gen.shortest_path())
        seed_label = (
            str(current_config.seed)
            if current_config.seed is not None
            else "rand"
        )
        rainbow_tag = " [RAINBOW]" if rainbow else ""
        print(
            f"{ANSI_BOLD}{wall_ansi}A-MAZE-ING{ANSI_RESET}  "
            f"{ANSI_DIM}|{ANSI_RESET} {current_config.width}x"
            f"{current_config.height} "
            f"{ANSI_DIM}|{ANSI_RESET} {mode_label} "
            f"{ANSI_DIM}|{ANSI_RESET} {current_config.algorithm} "
            f"{ANSI_DIM}|{ANSI_RESET} seed:{seed_label} "
            f"{ANSI_DIM}|{ANSI_RESET} path:{steps} "
            f"{ANSI_DIM}|{ANSI_RESET} {theme_name}{rainbow_tag}"
        )
        print(
            render_ascii(
                current_gen,
                show_path=show_path,
                wall_color_idx=wall_idx,
                pattern_color_idx=pattern_idx,
            )
        )
        print(
            f"\n{COLOR_ENTRY}\u25c6 Entry{ANSI_RESET}  "
            f"{COLOR_EXIT}\u2605 Exit{ANSI_RESET}  "
            f"{ANSI_DIM}[1/r] Regen  [2/p] Path  [3/c] Theme  "
            f"[t] 42  [b] Rainbow  [a] Algo  [v] Animate  "
            f"[4/q] Quit{ANSI_RESET}"
        )
        try:
            choice = input("Choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in {"1", "r"}:
            new_seed: Optional[int] = random.randrange(1_000_000)
            current_config = replace(current_config, seed=new_seed)
            current_gen = MazeGenerator(current_config)
            current_gen.generate(record_steps=True)
            current_gen.write_output(current_config.output_file)
        elif choice in {"2", "p"}:
            show_path = not show_path
        elif choice in {"3", "c"}:
            rainbow = False
            wall_idx = (wall_idx + 1) % len(WALL_THEMES)
        elif choice == "t":
            rainbow = False
            pattern_idx = (pattern_idx + 1) % len(PATTERN_COLORS)
        elif choice == "b":
            rainbow = not rainbow
        elif choice == "a":
            cur_idx = ALGORITHMS.index(current_config.algorithm)
            next_algo = ALGORITHMS[(cur_idx + 1) % len(ALGORITHMS)]
            current_config = replace(current_config, algorithm=next_algo)
            current_gen = MazeGenerator(current_config)
            current_gen.generate(record_steps=True)
            current_gen.write_output(current_config.output_file)
        elif choice == "v":
            _animate_ascii(
                current_config,
                current_gen,
                wall_idx,
                pattern_idx,
                clear_screen=clear_screen,
            )
        elif choice in {"4", "q"}:
            break


def _animate_ascii(
    config: MazeConfig,
    gen: MazeGenerator,
    wall_idx: int,
    pattern_idx: int,
    clear_screen: bool = True,
) -> None:
    """Play a brief terminal animation of maze carving."""
    if not gen.generation_steps:
        gen.generate(record_steps=True)
    preview = MazeGenerator(config)
    preview.grid = [
        [ALL_WALLS for _ in range(gen.width)] for _ in range(gen.height)
    ]
    steps = gen.generation_steps
    stride = max(1, len(steps) // 45)
    for idx, step in enumerate(steps):
        if step.cell_b is not None and step.direction is not None:
            r1, c1 = step.cell_a
            r2, c2 = step.cell_b
            preview.grid[r1][c1] &= ~int(step.direction)
            preview.grid[r2][c2] &= ~int(step.direction.opposite)
        if idx % stride == 0 or idx == len(steps) - 1:
            if clear_screen:
                print(ANSI_CLEAR, end="")
            print(
                render_ascii(
                    preview,
                    show_path=False,
                    wall_color_idx=wall_idx,
                    pattern_color_idx=pattern_idx,
                )
            )
            time.sleep(0.025)
