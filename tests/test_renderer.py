"""Unit tests for ASCII and MLX renderer state/rendering."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from mazegen.config import MazeConfig
from mazegen.generator import MazeGenerator
from mazegen.renderer_ascii import render_ascii
from mazegen.renderer_mlx import MazeSession, WALL_PALETTE


class TestRenderers(unittest.TestCase):
    """Verify ASCII rendering output and headless MLX session transitions."""

    def _make_session(self) -> tuple[MazeConfig, MazeGenerator]:
        """Build a temporary config and generated maze."""
        handle = tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False
        )
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        cfg = MazeConfig(
            width=12,
            height=10,
            entry=(0, 0),
            exit=(11, 9),
            output_file=handle.name,
            perfect=True,
            seed=42,
        )
        gen = MazeGenerator(cfg)
        gen.generate()
        return cfg, gen

    def test_ascii_render_dimensions(self) -> None:
        """ASCII canvas has 2*height + 1 lines."""
        _cfg, gen = self._make_session()
        rendered_no_path = render_ascii(gen, show_path=False)
        rendered_with_path = render_ascii(gen, show_path=True)
        self.assertEqual(len(rendered_no_path.splitlines()), 2 * 10 + 1)
        self.assertNotEqual(rendered_no_path, rendered_with_path)

    def test_mlx_session_controls(self) -> None:
        """MazeSession toggles path, rotates wall colors, and regenerates."""
        cfg, gen = self._make_session()
        session = MazeSession(cfg, gen, show_path=True)
        self.assertTrue(len(session.path_cell_set()) > 0)

        session.toggle_path()
        self.assertEqual(session.path_cell_set(), set())

        initial_color = session.wall_color
        session.cycle_wall_color()
        if len(WALL_PALETTE) > 1:
            self.assertNotEqual(session.wall_color, initial_color)

        old_rows = session.generator.to_hex_rows()
        session.regenerate(seed=999)
        self.assertNotEqual(session.generator.to_hex_rows(), old_rows)
        self.assertTrue(Path(cfg.output_file).exists())


if __name__ == "__main__":
    unittest.main()
