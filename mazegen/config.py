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


def _parse_int(raw: str, key: str) -> int:
    """Parse an integer value for a given configuration key."""
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(
            f"Invalid integer for {key}: {raw!r}."
        ) from exc


def _parse_bool(raw: str, key: str) -> bool:
    """Parse a boolean value for a given configuration key."""
    lowered = raw.strip().lower()
    if lowered in {"true", "1", "yes"}:
        return True
    if lowered in {"false", "0", "no"}:
        return False
    raise ConfigError(
        f"Invalid boolean for {key}: {raw!r} (expected True or False)."
    )


