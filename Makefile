VENV    := .venv
ifeq ($(OS),Windows_NT)
    PYTHON  := $(VENV)/Scripts/python
    PIP     := $(VENV)/Scripts/pip
else
    PYTHON  := $(VENV)/bin/python
    PIP     := $(VENV)/bin/pip
endif
STAMP   := $(VENV)/.installed

.DEFAULT_GOAL := all
.PHONY: all help install run clean distclean

## all         : install deps and start the zero-config launcher
all: install
	@$(MAKE) --no-print-directory run

## help        : print this summary
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## //'

# --- environment ---------------------------------------------------------

$(PYTHON):
	python3 -m venv $(VENV)

$(STAMP): requirements.txt | $(PYTHON)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
	@touch $(STAMP)

## install     : create .venv and install requirements.txt
install: $(STAMP)

# --- run ----------------------------------------------------------------

## run         : start the interactive TUI launcher
run: install
	$(PYTHON) src/launcher.py

# --- housekeeping -------------------------------------------------------

## clean       : remove Python bytecode caches
clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

## distclean   : clean + remove .venv
distclean: clean
	rm -rf $(VENV)
