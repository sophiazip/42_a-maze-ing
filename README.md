*This project has been created as part of the 42 curriculum by eroque-d.*

# A-Maze-ing

## Description

**A-Maze-ing** is a configurable maze generator, shortest-path solver, and interactive visualizer written in Python 3.10+. It produces either perfect mazes (spanning trees with a single unique path between any two cells) or playable Pac-Man-style braided boards (zero real dead-ends, multiple independent loops, accessible corners and center, and no $3 \times 3$ open areas), while embedding a closed `"42"` obstacle pattern in the center when grid dimensions allow.

The generation engine lives in a standalone installable package (`mazegen`) decoupled from the terminal ASCII and MiniLibX (MLX) graphical renderers.

---

## Instructions

### Setup and Installation

```bash
make install
```

To enable the graphical MLX renderer in a virtual environment on Ubuntu/Fedora:

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install --no-index --no-deps ../mlx-2.2/ubuntu/mlx-2.2-py3-none-any.whl
```

### Execution

Run with the default configuration file (`config.txt`):

```bash
make run
# or
python3 a_maze_ing.py config.txt
```

Override the visual mode from the command line:

```bash
python3 a_maze_ing.py config.txt --display ascii
python3 a_maze_ing.py config.txt --display mlx
```

### Interactive Controls

- **Terminal (`ascii`):**
  - `1` or `r`: Re-generate a new maze
  - `2` or `p`: Show / Hide the shortest path
  - `3` or `c`: Rotate wall colours
  - `t`: Rotate `"42"` pattern colour
  - `4` or `q`: Quit
- **GUI (`mlx`):**
  - `1` / `R`: Re-generate a new maze
  - `2` / `P`: Show / Hide the shortest path
  - `3` / `C`: Rotate wall colours
  - `T`: Rotate `"42"` pattern colour
  - `4` / `Q` / `Esc` / Window Close: Quit

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
| `PERFECT` | Yes | `PERFECT=True` | `True` for spanning tree, `False` for braided playable board |
| `SEED` | No | `SEED=42` | Integer seed for reproducible generation |
| `ALGORITHM` | No | `ALGORITHM=backtracker` | `backtracker`, `kruskal`, or `prim` |
| `DISPLAY` | No | `DISPLAY=ascii` | `ascii` or `mlx` |

---

## Algorithms and Design Choices

- **Iterative Recursive Backtracker (default):** Implemented with an explicit heap stack instead of Python recursion to avoid `RecursionError` on large grids. Produces long, winding corridors with natural flow.
- **Kruskal (with Disjoint Set Union) & Prim:** Included as alternative generators selectable via `ALGORITHM`, using path compression and union by rank in DSU for near-linear edge merging.
- **Playable Mode (`PERFECT=False`) & Braiding:** Starts from a connected spanning tree around the `"42"` cells, then eliminates real dead-ends and ensures cyclomatic complexity $L = E - V + 1 \ge 2$ while rejecting any wall removal that would create a $3 \times 3$ open area.
- **BFS Shortest Path:** Breadth-first search (`collections.deque`) guarantees the shortest sequence of `N`, `E`, `S`, `W` moves from `ENTRY` to `EXIT` in $O(V + E)$ time.

---

## Reusable Module (`mazegen`)

The `MazeGenerator` class is standalone and can be imported into future projects:

```python
from mazegen import MazeGenerator

gen = MazeGenerator(
    width=20,
    height=15,
    entry=(0, 0),
    exit=(19, 14),
    perfect=False,
    seed=42,
    algorithm="backtracker",
)
gen.generate()

# Access internal wall bitmask grid (row-major, bits: N=1, E=2, S=4, W=8)
grid = gen.grid
hex_rows = gen.to_hex_rows()

# Access shortest path as NESW string or ordered (x, y) coordinates
route = gen.shortest_path()
coords = gen.shortest_path_coords()

# Write subject-compliant output file
gen.write_output("maze.txt")
```

To build the installable wheel package from source:

```bash
python3 -m build
pip install dist/mazegen-1.0.0-py3-none-any.whl
```

---

## Team and Project Management

- **Planning & Documentation:** Organized on the `study-guides` branch with modular study guides, task breakdowns, risk matrices, and defense flashcards, tracked through 37 GitHub Issues.
- **Workflow:** Semantic micro-commits in English on dedicated feature/dev branches, paired with automated `flake8` and `mypy --strict` validation.
- **Tools:** Python 3.10, `flake8`, `mypy`, `unittest`, `maze_analyzer.py`, MiniLibX (`mlx-2.2`), and GitHub Issues.

---

## Resources and AI Usage

- **References:**
  - *Mazes for Programmers* (Jamis Buck) — Recursive Backtracker, Kruskal, Prim, and Braiding algorithms.
  - Python `enum.IntFlag`, `collections.deque`, and PEP 621 `pyproject.toml` documentation.
- **AI Usage:**
  - AI assistance was used to structure the `study-guides` planning documents, create GitHub issues, scaffold unit tests, and verify edge-case handling against `maze_analyzer.py` and `mypy --strict`.
