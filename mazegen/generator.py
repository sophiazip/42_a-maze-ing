"""Standalone maze generator module for A-Maze-ing."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import IntFlag
import random
import sys
from typing import Dict, Iterable, List, Optional, Set, Tuple

from mazegen.config import MazeConfig

Cell = Tuple[int, int]  # (row, col)
Coord = Tuple[int, int]  # (x, y)

PATTERN_42: Tuple[Tuple[int, ...], ...] = (
    (1, 0, 1, 0, 1, 1, 1),
    (1, 0, 1, 0, 0, 0, 1),
    (1, 1, 1, 0, 1, 1, 1),
    (0, 0, 1, 0, 1, 0, 0),
    (0, 0, 1, 0, 1, 1, 1),
)


class Direction(IntFlag):
    """Cardinal wall bitflags matching the hexadecimal output specification."""

    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8

    @property
    def opposite(self) -> "Direction":
        """Return the opposite cardinal direction."""
        return OPPOSITE_DIRECTION[self]

    @property
    def step(self) -> Cell:
        """Return the (d_row, d_col) offset for this direction."""
        return DIRECTION_STEPS[self]

    @property
    def letter(self) -> str:
        """Return the single-letter code ('N', 'E', 'S', 'W')."""
        return DIRECTION_LETTERS[self]


OPPOSITE_DIRECTION: Dict[Direction, Direction] = {
    Direction.NORTH: Direction.SOUTH,
    Direction.SOUTH: Direction.NORTH,
    Direction.EAST: Direction.WEST,
    Direction.WEST: Direction.EAST,
}

DIRECTION_STEPS: Dict[Direction, Cell] = {
    Direction.NORTH: (-1, 0),
    Direction.EAST: (0, 1),
    Direction.SOUTH: (1, 0),
    Direction.WEST: (0, -1),
}

DIRECTION_LETTERS: Dict[Direction, str] = {
    Direction.NORTH: "N",
    Direction.EAST: "E",
    Direction.SOUTH: "S",
    Direction.WEST: "W",
}

MOVE_OFFSETS: Dict[Direction, Coord] = {
    Direction.NORTH: (0, -1),
    Direction.EAST: (1, 0),
    Direction.SOUTH: (0, 1),
    Direction.WEST: (-1, 0),
}

ALL_WALLS: int = int(
    Direction.NORTH | Direction.EAST | Direction.SOUTH | Direction.WEST
)


@dataclass(frozen=True)
class GenerationStep:
    """Single carving or backtracking event captured during maze generation."""

    kind: str
    cell_a: Cell
    cell_b: Optional[Cell]
    direction: Optional[Direction]
    active: Cell


