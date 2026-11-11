"""Main CLI entry point for A-Maze-ing."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from mazegen.config import ConfigError, MazeConfig, parse_config
from mazegen.generator import MazeGenerator
from mazegen.renderer_ascii import run_ascii_loop
from mazegen.renderer_mlx import MazeWindow


def _build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="a_maze_ing.py",
        description="Generate, solve, and display a maze from a config file.",
    )
    parser.add_argument(
        "config",
        help="Path to the maze configuration file (e.g., config.txt).",
    )
    parser.add_argument(
        "--display",
        choices=("ascii", "mlx"),
        default=None,
        help="Override display mode ('ascii' or 'mlx').",
    )
    return parser


