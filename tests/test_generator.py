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

