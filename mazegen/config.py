"""Configuration file parser and validator for A-Maze-ing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

MANDATORY_KEYS = frozenset({
    "WIDTH",
    "HEIGHT",
    "ENTRY",
    "EXIT",
    "OUTPUT_FILE",
    "PERFECT",
})

OPTIONAL_KEYS = frozenset({"SEED", "ALGORITHM", "DISPLAY"})
VALID_ALGORITHMS = frozenset({"backtracker", "kruskal", "prim"})
VALID_DISPLAYS = frozenset({"ascii", "mlx"})


class ConfigError(Exception):
    """Raised when the configuration file is missing, malformed, or invalid."""


@dataclass(frozen=True)
class MazeConfig:
    """Validated maze generation and display configuration.

    Attributes:
        width: Maze width in cells.
        height: Maze height in cells.
        entry: Entry coordinates as (x, y).
        exit: Exit coordinates as (x, y).
        output_file: Path where the generated maze is written.
        perfect: True for a perfect maze, False for a playable board.
        seed: Optional integer seed for reproducible generation.
        algorithm: Generation algorithm name.
        display: Visual renderer mode ('ascii' or 'mlx').
    """

    width: int
    height: int
    entry: Tuple[int, int]
    exit: Tuple[int, int]
    output_file: str
    perfect: bool
    seed: Optional[int] = None
    algorithm: str = "backtracker"
    display: str = "ascii"


def _parse_int(raw: str, key: str) -> int:
    """Parse an integer value for a given configuration key."""
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(
            f"Invalid integer for {key}: {raw!r}."
        ) from exc


def _parse_bool(raw: str, key: str) -> bool:
    """Parse a boolean value for a given configuration key."""
    lowered = raw.strip().lower()
    if lowered in {"true", "1", "yes"}:
        return True
    if lowered in {"false", "0", "no"}:
        return False
    raise ConfigError(
        f"Invalid boolean for {key}: {raw!r} (expected True or False)."
    )


def _parse_coords(raw: str, key: str) -> Tuple[int, int]:
    """Parse an 'x,y' coordinate pair for a given configuration key."""
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 2:
        raise ConfigError(
            f"Invalid coordinates for {key}: {raw!r} (expected x,y)."
        )
    try:
        return int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ConfigError(
            f"Non-integer coordinates for {key}: {raw!r}."
        ) from exc


def _read_raw_pairs(path: str) -> Dict[str, str]:
    """Read raw KEY=VALUE pairs from a configuration file."""
    pairs: Dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as stream:
            for line_num, raw_line in enumerate(stream, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    raise ConfigError(
                        f"Line {line_num}: expected KEY=VALUE, got {line!r}."
                    )
                key, value = line.split("=", 1)
                key = key.strip().upper()
                value = value.strip()
                if not key:
                    raise ConfigError(
                        f"Line {line_num}: empty key before '='."
                    )
                if key not in MANDATORY_KEYS and key not in OPTIONAL_KEYS:
                    raise ConfigError(
                        f"Line {line_num}: unknown configuration key {key!r}."
                    )
                if key in pairs:
                    raise ConfigError(
                        f"Line {line_num}: duplicate key {key!r}."
                    )
                pairs[key] = value
    except OSError as exc:
        raise ConfigError(
            f"Could not read configuration file {path!r}: {exc.strerror}."
        ) from exc
    return pairs


def _validate_bounds(
    width: int,
    height: int,
    entry: Tuple[int, int],
    exit_: Tuple[int, int],
    output_file: str,
) -> None:
    """Validate semantic constraints on dimensions, coordinates, and path."""
    if width <= 0 or height <= 0:
        raise ConfigError(
            f"WIDTH and HEIGHT must be positive (got {width}x{height})."
        )
    ex, ey = entry
    if not (0 <= ex < width and 0 <= ey < height):
        raise ConfigError(
            f"ENTRY {entry} is out of bounds for {width}x{height} maze."
        )
    xx, xy = exit_
    if not (0 <= xx < width and 0 <= xy < height):
        raise ConfigError(
            f"EXIT {exit_} is out of bounds for {width}x{height} maze."
        )
    if entry == exit_:
        raise ConfigError(
            f"ENTRY and EXIT must be different cells (both are {entry})."
        )
    if not output_file:
        raise ConfigError("OUTPUT_FILE cannot be empty.")


def parse_config(path: str) -> MazeConfig:
    """Parse and validate a maze configuration file.

    Args:
        path: Path to the configuration file.

    Returns:
        A validated MazeConfig instance.

    Raises:
        ConfigError: If the file cannot be read or contains invalid settings.
    """
    pairs = _read_raw_pairs(path)
    missing = sorted(MANDATORY_KEYS - pairs.keys())
    if missing:
        raise ConfigError(
            f"Missing mandatory configuration keys: {', '.join(missing)}."
        )

    width = _parse_int(pairs["WIDTH"], "WIDTH")
    height = _parse_int(pairs["HEIGHT"], "HEIGHT")
    entry = _parse_coords(pairs["ENTRY"], "ENTRY")
    exit_ = _parse_coords(pairs["EXIT"], "EXIT")
    output_file = pairs["OUTPUT_FILE"]
    perfect = _parse_bool(pairs["PERFECT"], "PERFECT")

    _validate_bounds(width, height, entry, exit_, output_file)

    seed: Optional[int] = None
    if "SEED" in pairs and pairs["SEED"].lower() not in {"", "none"}:
        seed = _parse_int(pairs["SEED"], "SEED")

    algorithm = pairs.get("ALGORITHM", "backtracker").lower()
    if algorithm not in VALID_ALGORITHMS:
        raise ConfigError(
            f"Unsupported ALGORITHM {algorithm!r}. "
            f"Choose from: {', '.join(sorted(VALID_ALGORITHMS))}."
        )

    display = pairs.get("DISPLAY", "ascii").lower()
    if display not in VALID_DISPLAYS:
        raise ConfigError(
            f"Unsupported DISPLAY {display!r}. "
            f"Choose from: {', '.join(sorted(VALID_DISPLAYS))}."
        )

    return MazeConfig(
        width=width,
        height=height,
        entry=entry,
        exit=exit_,
        output_file=output_file,
        perfect=perfect,
        seed=seed,
        algorithm=algorithm,
        display=display,
    )
