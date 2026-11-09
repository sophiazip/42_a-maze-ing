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
