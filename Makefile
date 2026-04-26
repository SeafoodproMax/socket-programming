VENV    := .venv

ifeq ($(OS),Windows_NT)
    PYTHON_SYS := python
    PYTHON  := $(VENV)/Scripts/python.exe
    PIP     := $(VENV)/Scripts/pip.exe
    STAMP   := $(VENV)/.installed_win
else
    PYTHON_SYS := python3
    PYTHON  := $(VENV)/bin/python
    PIP     := $(VENV)/bin/pip
    STAMP   := $(VENV)/.installed_nix
endif

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
	$(PYTHON_SYS) -m venv $(VENV)

$(STAMP): requirements.txt | $(PYTHON)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
ifeq ($(OS),Windows_NT)
	@type NUL > $(STAMP)
else
	@touch $(STAMP)
endif

## install     : create .venv and install requirements.txt
install: $(STAMP)

# --- run ----------------------------------------------------------------

## run         : start the interactive TUI launcher
run: install
	$(PYTHON) src/launcher.py

# --- housekeeping -------------------------------------------------------

## clean       : remove Python bytecode caches
clean:
ifeq ($(OS),Windows_NT)
	-del /s /q *.pyc 2>NUL
	-for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>NUL
else
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
endif

## distclean   : clean + remove .venv
distclean: clean
ifeq ($(OS),Windows_NT)
	-rmdir /s /q $(VENV) 2>NUL
else
	rm -rf $(VENV)
endif
