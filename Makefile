PYTHON ?= python3
VENV := .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
RUN_PY := $(if $(wildcard $(VENV_PY)),$(VENV_PY),$(PYTHON))
CONFIG ?= config.txt

.PHONY: install run debug clean lint lint-strict

install:
	@if [ ! -d "$(VENV)" ]; then \
		$(PYTHON) -m venv --system-site-packages $(VENV); \
	fi
	$(VENV_PIP) install flake8 mypy pytest build
	@if [ -f "../mlx-2.2/ubuntu/mlx-2.2-py3-none-any.whl" ]; then \
		$(VENV_PIP) install --no-index --no-deps ../mlx-2.2/ubuntu/mlx-2.2-py3-none-any.whl; \
	fi

run:
	$(RUN_PY) a_maze_ing.py $(CONFIG)

debug:
	$(RUN_PY) -m pdb a_maze_ing.py $(CONFIG)

clean:
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache dist build *.egg-info

lint:
	flake8 .
	mypy . --exclude '^\.venv/' --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --exclude '^\.venv/' --strict
