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

