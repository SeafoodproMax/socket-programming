VENV    := .venv

# 強制指定 Shell，避免 Windows 抓到 git bash 的 sh.exe
ifeq ($(OS),Windows_NT)
    SHELL := cmd.exe
    V_BIN      := $(VENV)/Scripts
    PYTHON_SYS := python
    PYTHON     := $(V_BIN)/python.exe
    PIP        := $(V_BIN)/pip.exe
    STAMP      := .venv/.installed_win
    # 指令適配
    MKDIR      := mkdir
    RM         := del /q /f
    RMDIR      := rmdir /s /q
    # Windows CMD 建立空檔案的寫法
    TOUCH      := copy /y NUL >
    FIX_PATH    = $(subst /,\,$1)
else
    # Mac / Linux 邏輯 (保持不變)
    SHELL      := /bin/sh
    V_BIN      := $(VENV)/bin
    PYTHON_SYS := python3
    PYTHON     := $(V_BIN)/python
    PIP        := $(V_BIN)/pip
    STAMP      := .venv/.installed_nix
    MKDIR      := mkdir -p
    RM         := rm -f
    RMDIR      := rm -rf
    TOUCH      := touch
    FIX_PATH    = $1
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

# 用一個虛擬 target 確保 venv 存在
$(PYTHON):
	$(PYTHON_SYS) -m venv $(VENV)

# 安裝依賴並建立 Stamp
$(STAMP): requirements.txt | $(PYTHON)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
	@$(TOUCH) $(call FIX_PATH,$(STAMP))

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
	-$(RMDIR) $(call FIX_PATH,$(VENV))