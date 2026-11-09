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


class _DisjointSetUnion:
    """Union-Find structure with path compression and union by rank."""

    def __init__(self, items: Iterable[Cell]) -> None:
        """Initialize each item as its own singleton set."""
        self._parent: Dict[Cell, Cell] = {item: item for item in items}
        self._rank: Dict[Cell, int] = {item: 0 for item in items}

    def find(self, item: Cell) -> Cell:
        """Return the representative root of item's set."""
        root = item
        while self._parent[root] != root:
            root = self._parent[root]
        curr = item
        while curr != root:
            nxt = self._parent[curr]
            self._parent[curr] = root
            curr = nxt
        return root

    def union(self, first: Cell, second: Cell) -> bool:
        """Merge two sets; return False if they already share a root."""
        root_a = self.find(first)
        root_b = self.find(second)
        if root_a == root_b:
            return False
        if self._rank[root_a] < self._rank[root_b]:
            self._parent[root_a] = root_b
        elif self._rank[root_a] > self._rank[root_b]:
            self._parent[root_b] = root_a
        else:
            self._parent[root_b] = root_a
            self._rank[root_a] += 1
        return True


class MazeGenerator:
    """Configurable maze generator supporting perfect and braided modes.

    Can be instantiated either from a :class:`MazeConfig` object or via keyword
    parameters for standalone reuse in external projects.
    """

    def __init__(
        self,
        config: Optional[MazeConfig] = None,
        *,
        width: int = 20,
        height: int = 15,
        entry: Coord = (0, 0),
        exit: Coord = (19, 14),
        perfect: bool = True,
        seed: Optional[int] = None,
        algorithm: str = "backtracker",
    ) -> None:
        """Initialize the maze grid and reserve the '42' obstacle cells."""
        if config is not None:
            self.width = config.width
            self.height = config.height
            self.entry = config.entry
            self.exit = config.exit
            self.perfect = config.perfect
            self.seed = config.seed
            self.algorithm = config.algorithm
        else:
            self.width = width
            self.height = height
            self.entry = entry
            self.exit = exit
            self.perfect = perfect
            self.seed = seed
            self.algorithm = algorithm

        self._validate_dimensions()
        self._rng = random.Random(self.seed)
        self.grid: List[List[int]] = [
            [ALL_WALLS for _ in range(self.width)] for _ in range(self.height)
        ]
        self.blocked_cells: Set[Cell] = self._compute_pattern_cells()
        self.generation_steps: List[GenerationStep] = []
        self._record_steps = False
        self._generated = False

    def _validate_dimensions(self) -> None:
        """Ensure maze dimensions and entry/exit coordinates are valid."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Maze width and height must be positive.")
        ex, ey = self.entry
        xx, xy = self.exit
        if not (0 <= ex < self.width and 0 <= ey < self.height):
            raise ValueError("Entry coordinates are out of bounds.")
        if not (0 <= xx < self.width and 0 <= xy < self.height):
            raise ValueError("Exit coordinates are out of bounds.")
        if self.entry == self.exit:
            raise ValueError("Entry and exit must be distinct cells.")

    @property
    def entry_cell(self) -> Cell:
        """Return entry position as internal (row, col)."""
        return (self.entry[1], self.entry[0])

    @property
    def exit_cell(self) -> Cell:
        """Return exit position as internal (row, col)."""
        return (self.exit[1], self.exit[0])

    def _in_bounds(self, row: int, col: int) -> bool:
        """Return True when (row, col) lies within the grid."""
        return 0 <= row < self.height and 0 <= col < self.width

    def _compute_pattern_cells(self) -> Set[Cell]:
        """Compute centered '42' cells, omitting with notice if too small."""
        pat_h = len(PATTERN_42)
        pat_w = len(PATTERN_42[0])
        if self.height < pat_h + 2 or self.width < pat_w + 2:
            print(
                f"Notice: maze size ({self.width}x{self.height}) is too small "
                "for the '42' pattern; pattern omitted.",
                file=sys.stderr,
            )
            return set()

        top = (self.height - pat_h) // 2
        left = (self.width - pat_w) // 2
        cells: Set[Cell] = set()
        for r_off, pat_row in enumerate(PATTERN_42):
            for c_off, bit in enumerate(pat_row):
                if bit:
                    cells.add((top + r_off, left + c_off))

        if self.entry_cell in cells or self.exit_cell in cells:
            print(
                "Notice: entry or exit overlaps the centered '42' pattern; "
                "pattern omitted.",
                file=sys.stderr,
            )
            return set()
        return cells

