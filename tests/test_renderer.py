"""Unit tests for ASCII and MLX renderer state/rendering."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from mazegen.config import MazeConfig
from mazegen.generator import MazeGenerator
from mazegen.renderer_ascii import render_ascii
from mazegen.session import MazeSession, WALL_PALETTE


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

