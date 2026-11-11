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

