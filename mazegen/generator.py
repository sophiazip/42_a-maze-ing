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

    def _record_step(
        self,
        kind: str,
        cell_a: Cell,
        cell_b: Optional[Cell],
        direction: Optional[Direction],
        active: Cell,
    ) -> None:
        """Append a generation event when step recording is enabled."""
        if self._record_steps:
            self.generation_steps.append(
                GenerationStep(
                    kind=kind,
                    cell_a=cell_a,
                    cell_b=cell_b,
                    direction=direction,
                    active=active,
                )
            )

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
                self._record_step("carve", current, nxt, direction, nxt)
                visited.add(nxt)
                stack.append(nxt)
            else:
                popped = stack.pop()
                if stack:
                    self._record_step(
                        "backtrack", popped, stack[-1], None, stack[-1]
                    )

    def _run_kruskal(self) -> None:
        """Carve a spanning tree using randomized Kruskal with DSU."""
        playable = [
            (r, c)
            for r in range(self.height)
            for c in range(self.width)
            if (r, c) not in self.blocked_cells
        ]
        dsu = _DisjointSetUnion(playable)
        edges: List[Tuple[Cell, Cell, Direction]] = []
        for row, col in playable:
            for direction in (Direction.EAST, Direction.SOUTH):
                dr, dc = direction.step
                nr, nc = row + dr, col + dc
                if (
                    self._in_bounds(nr, nc)
                    and (nr, nc) not in self.blocked_cells
                ):
                    edges.append(((row, col), (nr, nc), direction))

        self._rng.shuffle(edges)
        for cell_a, cell_b, direction in edges:
            if dsu.union(cell_a, cell_b):
                self._remove_wall(cell_a, cell_b, direction)
                self._record_step("carve", cell_a, cell_b, direction, cell_b)

    def _run_prim(self) -> None:
        """Carve a spanning tree using randomized Prim's frontier."""
        visited: Set[Cell] = set(self.blocked_cells)
        start = self.entry_cell
        visited.add(start)
        frontier: List[Tuple[Cell, Cell, Direction]] = [
            (start, nxt, direction)
            for direction, nxt in self._neighbors(start)
        ]

        while frontier:
            idx = self._rng.randrange(len(frontier))
            frontier[idx], frontier[-1] = frontier[-1], frontier[idx]
            cell_a, cell_b, direction = frontier.pop()
            if cell_b in visited:
                continue
            self._remove_wall(cell_a, cell_b, direction)
            self._record_step("carve", cell_a, cell_b, direction, cell_b)
            visited.add(cell_b)
            for next_dir, nxt in self._neighbors(cell_b):
                if nxt not in visited:
                    frontier.append((cell_b, nxt, next_dir))

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
                        self._record_step("carve", cell, nxt, direction, nxt)
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
                    self._record_step("braid", cell, nxt, direction, nxt)
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
                        self._record_step("braid", cell, nxt, direction, nxt)
                        break

    def generate(self, record_steps: bool = False) -> None:
        """Generate the maze according to the configured mode and algorithm."""
        self.grid = [
            [ALL_WALLS for _ in range(self.width)] for _ in range(self.height)
        ]
        self.generation_steps = []
        self._record_steps = record_steps
        try:
            if self.algorithm == "kruskal":
                self._run_kruskal()
            elif self.algorithm == "prim":
                self._run_prim()
            else:
                self._run_backtracker()

            self._ensure_full_connectivity()
            if not self.perfect:
                self._braid_and_add_loops()
        finally:
            self._record_steps = False
        self._generated = True

    def _bfs_solve(self) -> Tuple[List[Cell], List[Cell], str]:
        """Run BFS from entry to exit, returning explored, path cells, NESW."""
        start = self.entry_cell
        target = self.exit_cell
        queue: deque[Cell] = deque([start])
        parent: Dict[Cell, Tuple[Cell, Direction]] = {}
        seen: Set[Cell] = {start}
        explored: List[Cell] = [start]

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
                        explored.append(nxt)
                        parent[nxt] = (curr, direction)
                        queue.append(nxt)

        if target not in parent and target != start:
            return explored, [], ""

        letters: List[str] = []
        cells: List[Cell] = [target]
        curr = target
        while curr != start:
            prev, direction = parent[curr]
            letters.append(direction.letter)
            cells.append(prev)
            curr = prev
        letters.reverse()
        cells.reverse()
        return explored, cells, "".join(letters)

    def shortest_path(self) -> str:
        """Compute the shortest valid path from entry to exit as NESW text."""
        _explored, _cells, route = self._bfs_solve()
        return route

    def solve_with_trace(self) -> Tuple[List[Cell], List[Cell]]:
        """Return (explored_cells, shortest_path_cells) for animation."""
        explored, cells, _route = self._bfs_solve()
        return explored, cells

