"""Interactive MiniLibX (MLX) architectural renderer for A-Maze-ing."""

from __future__ import annotations

import importlib
import time
from typing import Any, List, Tuple

from mazegen.config import MazeConfig
from mazegen.generator import Direction, MazeGenerator
from mazegen.session import MazeSession
from mazegen.sound import ChiptunePlayer

_mlx: Any = None
MLX_AVAILABLE = False
try:
    _mlx = importlib.import_module("mlx")
    MLX_AVAILABLE = True
except ImportError:
    pass

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

