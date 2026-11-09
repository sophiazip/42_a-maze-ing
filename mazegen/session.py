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
