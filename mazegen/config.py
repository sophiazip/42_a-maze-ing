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


class ConfigError(Exception):
    """Raised when the configuration file is missing, malformed, or invalid."""


@dataclass(frozen=True)
class MazeConfig:
    """Validated maze generation and display configuration.

    Attributes:
        width: Maze width in cells.
        height: Maze height in cells.
        entry: Entry coordinates as (x, y).
        exit: Exit coordinates as (x, y).
        output_file: Path where the generated maze is written.
        perfect: True for a perfect maze, False for a playable board.
        seed: Optional integer seed for reproducible generation.
        algorithm: Generation algorithm name.
        display: Visual renderer mode ('ascii' or 'mlx').
    """

    width: int
    height: int
    entry: Tuple[int, int]
    exit: Tuple[int, int]
    output_file: str
    perfect: bool
    seed: Optional[int] = None
    algorithm: str = "backtracker"
    display: str = "ascii"


