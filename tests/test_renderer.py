"""Unit tests for the terminal ASCII renderer."""

from __future__ import annotations

import unittest

from mazegen.generator import MazeGenerator
from mazegen.renderer_ascii import render_ascii


class TestAsciiRenderer(unittest.TestCase):
    """Verify ASCII rendering dimensions and shortest-path toggle."""

    def test_ascii_render_dimensions_and_path(self) -> None:
        """ASCII canvas has 2*height + 1 lines and toggles path markers."""
        gen = MazeGenerator(
            width=12,
            height=10,
            entry=(0, 0),
            exit=(11, 9),
            perfect=True,
            seed=42,
        )
        gen.generate()
        rendered_no_path = render_ascii(gen, show_path=False)
        rendered_with_path = render_ascii(gen, show_path=True)
        self.assertEqual(len(rendered_no_path.splitlines()), 2 * 10 + 1)
        self.assertNotEqual(rendered_no_path, rendered_with_path)


if __name__ == "__main__":
    unittest.main()
