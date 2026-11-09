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
