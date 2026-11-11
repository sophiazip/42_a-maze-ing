*This project has been created as part of the 42 curriculum by eroque-d, jumoreir.*

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

