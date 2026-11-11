"""Unit tests for mazegen.config."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from mazegen.config import ConfigError, parse_config


class TestConfigParser(unittest.TestCase):
    """Verify valid parsing and semantic validation of config files."""

    def _write_temp(self, content: str) -> str:
        """Write temporary config text and return its path."""
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        handle.write(content)
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return handle.name

    def test_valid_config_parses(self) -> None:
        """Valid mandatory and optional keys return a MazeConfig."""
        path = self._write_temp(
            "# Sample comment\n"
            "WIDTH=20\n"
            "HEIGHT=15\n"
            "ENTRY=0,0\n"
            "EXIT=19,14\n"
            "OUTPUT_FILE=maze.txt\n"
            "PERFECT=False\n"
            "SEED=42\n"
            "ALGORITHM=kruskal\n"
            "DISPLAY=mlx\n"
        )
        cfg = parse_config(path)
        self.assertEqual(cfg.width, 20)
        self.assertEqual(cfg.height, 15)
        self.assertEqual(cfg.entry, (0, 0))
        self.assertEqual(cfg.exit, (19, 14))
        self.assertEqual(cfg.output_file, "maze.txt")
        self.assertFalse(cfg.perfect)
        self.assertEqual(cfg.seed, 42)
        self.assertEqual(cfg.algorithm, "kruskal")
        self.assertEqual(cfg.display, "mlx")

    def test_missing_file_raises_config_error(self) -> None:
        """Non-existent path raises ConfigError."""
        with self.assertRaises(ConfigError):
            parse_config("/tmp/non_existent_a_maze_ing_cfg.txt")

    def test_missing_mandatory_key_raises(self) -> None:
        """Missing EXIT key raises ConfigError."""
        path = self._write_temp(
            "WIDTH=10\nHEIGHT=10\nENTRY=0,0\n"
            "OUTPUT_FILE=out.txt\nPERFECT=True\n"
        )
        with self.assertRaises(ConfigError):
            parse_config(path)

