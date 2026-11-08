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

