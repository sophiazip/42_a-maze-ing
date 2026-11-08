"""Configuration file parser and validator for A-Maze-ing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

MANDATORY_KEYS = frozenset({
    "WIDTH",
    "HEIGHT",
    "ENTRY",
    "EXIT",
    "OUTPUT_FILE",
    "PERFECT",
})

OPTIONAL_KEYS = frozenset({"SEED", "ALGORITHM", "DISPLAY"})
ALGORITHMS: Tuple[str, ...] = ("backtracker", "kruskal", "prim")
VALID_ALGORITHMS = frozenset(ALGORITHMS)
VALID_DISPLAYS = frozenset({"ascii", "mlx"})


