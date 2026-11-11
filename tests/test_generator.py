"""Unit tests for mazegen.generator."""

from __future__ import annotations

import unittest

from mazegen.generator import (
    ALL_WALLS,
    DIRECTION_STEPS,
    Direction,
    MazeGenerator,
    pick_random_endpoints,
)


class TestMazeGenerator(unittest.TestCase):
    """Verify wall coherence, modes, algorithms, and BFS pathfinding."""

    def _assert_coherent(self, gen: MazeGenerator) -> None:
        """Assert every shared wall agrees on both neighbouring cells."""
        for r in range(gen.height):
            for c in range(gen.width):
                mask = gen.grid[r][c]
                for direction in Direction:
                    dr, dc = direction.step
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < gen.height and 0 <= nc < gen.width:
                        n_mask = gen.grid[nr][nc]
                        self.assertEqual(
                            bool(mask & int(direction)),
                            bool(n_mask & int(direction.opposite)),
                        )

    def _assert_no_3x3_open(self, gen: MazeGenerator) -> None:
        """Assert no 3x3 subgrid is completely free of internal walls."""
        for r in range(gen.height - 2):
            for c in range(gen.width - 2):
                all_open = True
                for dr in range(3):
                    for dc in range(3):
                        if dc < 2 and (
                            gen.grid[r + dr][c + dc] & int(Direction.EAST)
                        ):
                            all_open = False
                        if dr < 2 and (
                            gen.grid[r + dr][c + dc] & int(Direction.SOUTH)
                        ):
                            all_open = False
                self.assertFalse(all_open)

    def test_seed_reproducibility(self) -> None:
        """Identical seeds produce identical hexadecimal grids and paths."""
        g1 = MazeGenerator(width=15, height=12, exit=(14, 11), seed=1234)
        g2 = MazeGenerator(width=15, height=12, exit=(14, 11), seed=1234)
        g1.generate()
        g2.generate()
        self.assertEqual(g1.to_hex_rows(), g2.to_hex_rows())
        self.assertEqual(g1.shortest_path(), g2.shortest_path())

    def test_algorithms_perfect_and_playable(self) -> None:
        """All algorithms pass coherence, connectivity, and 3x3 checks."""
        for algo in ("backtracker", "kruskal", "prim"):
            for perfect in (True, False):
                gen = MazeGenerator(
                    width=20,
                    height=15,
                    entry=(0, 0),
                    exit=(19, 14),
                    perfect=perfect,
                    seed=99,
                    algorithm=algo,
                )
                gen.generate()
                self._assert_coherent(gen)
                self._assert_no_3x3_open(gen)
                path = gen.shortest_path()
                self.assertTrue(len(path) > 0)
                self._trace_path(gen, path)

    def _trace_path(self, gen: MazeGenerator, path: str) -> None:
        """Verify each step in path crosses an open wall and hits exit."""
        letter_to_dir = {d.letter: d for d in Direction}
        row, col = gen.entry_cell
        for char in path:
            direction = letter_to_dir[char]
            self.assertFalse(gen.grid[row][col] & int(direction))
            dr, dc = DIRECTION_STEPS[direction]
            row += dr
            col += dc
        self.assertEqual((row, col), gen.exit_cell)

