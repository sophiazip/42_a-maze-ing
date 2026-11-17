*This project has been created as part of the 42 curriculum by eroque-d, jumoreir.*

# A-Maze-ing

## Description

**A-Maze-ing** is a configurable maze generator, shortest-path solver, and interactive terminal visualizer written in Python 3.10+. It produces either perfect mazes (spanning trees with a single unique path between any two cells) or non-perfect mazes with loops and no $3 \times 3$ open areas, while embedding a closed `"42"` obstacle pattern in the center when grid dimensions allow.

The generation engine lives in a standalone installable package (`mazegen`) decoupled from the terminal ASCII renderer.

---

## Instructions

### Setup and Installation

```bash
make install
```

### Execution

Run with the default configuration file (`config.txt`):

```bash
make run
# or
python3 a_maze_ing.py config.txt
```

### Interactive Terminal Controls

- `1` or `r`: Re-generate a new maze
- `2` or `p`: Show / Hide the shortest path
- `3` or `c`: Rotate wall colours
- `t`: Rotate `"42"` pattern colour
- `4` or `q`: Quit

### Quality and Testing

```bash
make lint
make lint-strict
python3 -m unittest discover -s tests -v
```

---

## Configuration File Format

Each line uses `KEY=VALUE`. Blank lines and lines starting with `#` are ignored.

| Key | Required | Example | Description |
| :--- | :--- | :--- | :--- |
| `WIDTH` | Yes | `WIDTH=20` | Maze width in cells |
| `HEIGHT` | Yes | `HEIGHT=15` | Maze height in cells |
| `ENTRY` | Yes | `ENTRY=0,0` | Entry coordinates `(x,y)` |
| `EXIT` | Yes | `EXIT=19,14` | Exit coordinates `(x,y)` |
| `OUTPUT_FILE` | Yes | `OUTPUT_FILE=maze.txt` | Output file path |
| `PERFECT` | Yes | `PERFECT=True` | `True` for spanning tree, `False` for maze with loops |
| `SEED` | No | `SEED=42` | Integer seed for reproducible generation |

---

## Algorithms and Design Choices

- **Iterative Recursive Backtracker:** Implemented with an explicit heap stack instead of Python recursion to avoid `RecursionError` on large grids. Produces long, winding corridors.
- **Non-Perfect Mode (`PERFECT=False`):** Starts from a connected spanning tree around the `"42"` cells, then removes selected walls to introduce loops ($L = E - V + 1 \ge 2$) while rejecting any wall removal that would create a $3 \times 3$ open area.
- **BFS Shortest Path:** Breadth-first search (`collections.deque`) guarantees the shortest sequence of `N`, `E`, `S`, `W` moves from `ENTRY` to `EXIT` in $O(V + E)$ time.

---

## Reusable Module (`mazegen`)

```python
from mazegen import MazeGenerator

gen = MazeGenerator(
    width=20,
    height=15,
    entry=(0, 0),
    exit=(19, 14),
    perfect=True,
    seed=42,
)
gen.generate()

grid = gen.grid
hex_rows = gen.to_hex_rows()
route = gen.shortest_path()
gen.write_output("maze.txt")
```

To build the installable wheel package from source:

```bash
python3 -m build
pip install dist/mazegen-1.0.0-py3-none-any.whl
```

---

## Resources and AI Usage

- **References:**
  - *Mazes for Programmers* (Jamis Buck) — Recursive Backtracker and Braiding algorithms.
  - Python `enum.IntFlag`, `collections.deque`, and PEP 621 `pyproject.toml` documentation.
- **AI Usage:**
  - AI assistance was used to structure planning documents, scaffold unit tests, and verify edge-case handling against `flake8` and `mypy --strict`.
