"""Interactive terminal box-drawing ANSI renderer for A-Maze-ing."""

from __future__ import annotations

from dataclasses import replace
import random
import time
from typing import Dict, List, Optional, Set, Tuple

from mazegen.config import ALGORITHMS, MazeConfig
from mazegen.generator import (
    ALL_WALLS,
    Direction,
    MazeGenerator,
    pick_random_endpoints,
)

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


