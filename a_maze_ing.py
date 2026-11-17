"""Main CLI entry point for A-Maze-ing."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from mazegen.config import ConfigError, parse_config
from mazegen.generator import MazeGenerator
from mazegen.renderer_ascii import run_ascii_loop


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
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Parse arguments, generate the maze, write output, and launch UI."""
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1

    try:
        config = parse_config(args.config)
        generator = MazeGenerator(config)
        generator.generate()
        generator.write_output(config.output_file)
    except (ConfigError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        run_ascii_loop(config, generator)
    except Exception as exc:
        print(f"Display error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
