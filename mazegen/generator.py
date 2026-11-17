"""Standalone maze generator module for A-Maze-ing."""

from __future__ import annotations

from collections import deque
from enum import IntFlag
import random
import sys
from typing import Dict, List, Optional, Set, Tuple

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
    ) -> None:
        """Initialize the maze grid and reserve the '42' obstacle cells."""
        if config is not None:
            self.width = config.width
            self.height = config.height
            self.entry = config.entry
            self.exit = config.exit
            self.perfect = config.perfect
            self.seed = config.seed
        else:
            self.width = width
            self.height = height
            self.entry = entry
            self.exit = exit
            self.perfect = perfect
            self.seed = seed

        self._validate_dimensions()
        self._rng = random.Random(self.seed)
        self.grid: List[List[int]] = [
            [ALL_WALLS for _ in range(self.width)] for _ in range(self.height)
        ]
        self.blocked_cells: Set[Cell] = self._compute_pattern_cells()
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

    def _remove_wall(
        self,
        cell_a: Cell,
        cell_b: Cell,
        direction: Direction,
    ) -> None:
        """Open the shared wall between two adjacent cells atomically."""
        r1, c1 = cell_a
        r2, c2 = cell_b
        self.grid[r1][c1] &= ~int(direction)
        self.grid[r2][c2] &= ~int(direction.opposite)

    def _neighbors(self, cell: Cell) -> List[Tuple[Direction, Cell]]:
        """Return in-bounds non-blocked neighbours with their directions."""
        row, col = cell
        result: List[Tuple[Direction, Cell]] = []
        for direction in Direction:
            dr, dc = direction.step
            nr, nc = row + dr, col + dc
            if self._in_bounds(nr, nc) and (nr, nc) not in self.blocked_cells:
                result.append((direction, (nr, nc)))
        return result

    def _run_backtracker(self) -> None:
        """Carve a spanning tree using an iterative DFS stack."""
        visited: Set[Cell] = set(self.blocked_cells)
        start = self.entry_cell
        stack: List[Cell] = [start]
        visited.add(start)

        while stack:
            current = stack[-1]
            unvisited = [
                (direction, nxt)
                for direction, nxt in self._neighbors(current)
                if nxt not in visited
            ]
            if unvisited:
                direction, nxt = self._rng.choice(unvisited)
                self._remove_wall(current, nxt, direction)
                visited.add(nxt)
                stack.append(nxt)
            else:
                stack.pop()

    def _ensure_full_connectivity(self) -> None:
        """Connect any disconnected playable components to entry's region."""
        playable = {
            (r, c)
            for r in range(self.height)
            for c in range(self.width)
            if (r, c) not in self.blocked_cells
        }
        while True:
            reachable = self._reachable_from(self.entry_cell)
            missing = playable - reachable
            if not missing:
                break
            bridged = False
            for cell in sorted(missing):
                for direction, nxt in self._neighbors(cell):
                    if nxt in reachable:
                        self._remove_wall(cell, nxt, direction)
                        bridged = True
                        break
                if bridged:
                    break
            if not bridged:
                break

    def _reachable_from(self, start: Cell) -> Set[Cell]:
        """Return all cells reachable from start via open passages."""
        seen: Set[Cell] = {start}
        queue: deque[Cell] = deque([start])
        while queue:
            curr = queue.popleft()
            row, col = curr
            for direction in Direction:
                if not (self.grid[row][col] & int(direction)):
                    dr, dc = direction.step
                    nxt = (row + dr, col + dc)
                    if self._in_bounds(*nxt) and nxt not in seen:
                        seen.add(nxt)
                        queue.append(nxt)
        return seen

    def _is_square_fully_open(self, top_row: int, left_col: int) -> bool:
        """Return True if a 3x3 block has all internal walls removed."""
        for dr in range(3):
            for dc in range(3):
                r, c = top_row + dr, left_col + dc
                if dc < 2 and (self.grid[r][c] & int(Direction.EAST)):
                    return False
                if dr < 2 and (self.grid[r][c] & int(Direction.SOUTH)):
                    return False
        return True

    def _creates_open_area(
        self,
        cell_a: Cell,
        cell_b: Cell,
        direction: Direction,
    ) -> bool:
        """Return True if opening cell_a <-> cell_b creates a 3x3 open area."""
        r1, c1 = cell_a
        r2, c2 = cell_b
        self.grid[r1][c1] &= ~int(direction)
        self.grid[r2][c2] &= ~int(direction.opposite)

        min_r = max(0, min(r1, r2) - 2)
        max_r = min(self.height - 3, max(r1, r2))
        min_c = max(0, min(c1, c2) - 2)
        max_c = min(self.width - 3, max(c1, c2))

        creates = False
        for top_r in range(min_r, max_r + 1):
            for left_c in range(min_c, max_c + 1):
                if self._is_square_fully_open(top_r, left_c):
                    creates = True
                    break
            if creates:
                break

        self.grid[r1][c1] |= int(direction)
        self.grid[r2][c2] |= int(direction.opposite)
        return creates

    def _open_passages_count(self, cell: Cell) -> int:
        """Return the number of open passages leaving cell."""
        row, col = cell
        return sum(
            1
            for direction in Direction
            if not (self.grid[row][col] & int(direction))
        )

    def _closed_normal_neighbors(
        self,
        cell: Cell,
    ) -> List[Tuple[Direction, Cell]]:
        """Return closed walls bordering a playable neighbour."""
        row, col = cell
        candidates: List[Tuple[Direction, Cell]] = []
        for direction, nxt in self._neighbors(cell):
            if self.grid[row][col] & int(direction):
                candidates.append((direction, nxt))
        return candidates

    def _loop_count(self) -> int:
        """Compute cyclomatic complexity (edges - nodes + 1) of the maze."""
        playable = [
            (r, c)
            for r in range(self.height)
            for c in range(self.width)
            if (r, c) not in self.blocked_cells
        ]
        edges = 0
        for row, col in playable:
            for direction in (Direction.EAST, Direction.SOUTH):
                if not (self.grid[row][col] & int(direction)):
                    dr, dc = direction.step
                    if self._in_bounds(row + dr, col + dc):
                        edges += 1
        return edges - len(playable) + 1

    def _braid_and_add_loops(self) -> None:
        """Eliminate real dead-ends and guarantee at least two loops."""
        playable = [
            (r, c)
            for r in range(self.height)
            for c in range(self.width)
            if (r, c) not in self.blocked_cells
        ]
        self._rng.shuffle(playable)

        for cell in playable:
            if self._open_passages_count(cell) != 1:
                continue
            candidates = self._closed_normal_neighbors(cell)
            self._rng.shuffle(candidates)
            # Prefer merging two dead-ends to reduce dead-end count faster.
            candidates.sort(
                key=lambda item: self._open_passages_count(item[1]) != 1
            )
            for direction, nxt in candidates:
                if not self._creates_open_area(cell, nxt, direction):
                    self._remove_wall(cell, nxt, direction)
                    break

        if self._loop_count() < 2:
            self._rng.shuffle(playable)
            for cell in playable:
                if self._loop_count() >= 2:
                    break
                candidates = self._closed_normal_neighbors(cell)
                self._rng.shuffle(candidates)
                for direction, nxt in candidates:
                    if not self._creates_open_area(cell, nxt, direction):
                        self._remove_wall(cell, nxt, direction)
                        break

    def generate(self) -> None:
        """Generate the maze using iterative recursive backtracker."""
        self.grid = [
            [ALL_WALLS for _ in range(self.width)] for _ in range(self.height)
        ]
        self._run_backtracker()
        self._ensure_full_connectivity()
        if not self.perfect:
            self._braid_and_add_loops()
        self._generated = True

    def shortest_path(self) -> str:
        """Compute the shortest valid path from entry to exit as NESW text."""
        start = self.entry_cell
        target = self.exit_cell
        queue: deque[Cell] = deque([start])
        parent: Dict[Cell, Tuple[Cell, Direction]] = {}
        seen: Set[Cell] = {start}

        while queue:
            curr = queue.popleft()
            if curr == target:
                break
            row, col = curr
            for direction in Direction:
                if not (self.grid[row][col] & int(direction)):
                    dr, dc = direction.step
                    nxt = (row + dr, col + dc)
                    if self._in_bounds(*nxt) and nxt not in seen:
                        seen.add(nxt)
                        parent[nxt] = (curr, direction)
                        queue.append(nxt)

        if target not in parent and target != start:
            return ""

        letters: List[str] = []
        curr = target
        while curr != start:
            prev, direction = parent[curr]
            letters.append(direction.letter)
            curr = prev
        letters.reverse()
        return "".join(letters)

    def shortest_path_coords(self) -> List[Coord]:
        """Return ordered (x, y) coordinates along the shortest path."""
        x, y = self.entry
        coords: List[Coord] = [(x, y)]
        letter_map = {d.letter: d for d in Direction}
        for char in self.shortest_path():
            direction = letter_map.get(char)
            if direction is None:
                break
            dx, dy = MOVE_OFFSETS[direction]
            x += dx
            y += dy
            coords.append((x, y))
        return coords

    def to_hex_rows(self) -> List[str]:
        """Serialize the maze grid as uppercase hexadecimal strings."""
        return [
            "".join(f"{cell:X}" for cell in row)
            for row in self.grid
        ]

    def write_output(self, filepath: str, path: Optional[str] = None) -> None:
        """Write the hexadecimal grid, coordinates, and shortest path."""
        route = self.shortest_path() if path is None else path
        lines = self.to_hex_rows()
        lines.append("")
        lines.append(f"{self.entry[0]},{self.entry[1]}")
        lines.append(f"{self.exit[0]},{self.exit[1]}")
        lines.append(route)
        with open(filepath, "w", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")
