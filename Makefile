VENV    := .venv
PYTHON  := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip
STAMP   := $(VENV)/.installed
CONFIG  := config/host.yaml

# Which server_list profile to use at runtime. Override on the command line:
#   make server PROFILE=lab_server
PROFILE ?= self
# Profile name that `make reconfig` upserts (defaults to the runtime PROFILE).
NAME    ?= $(PROFILE)

.DEFAULT_GOAL := all
.PHONY: all help install config reconfig server multiserver client auto-client clean distclean

## all         : install deps, upsert 'self' profile into $(CONFIG) (if missing), show next steps
all: install $(CONFIG)
	@echo ""
	@echo "Ready. Pick one:"
	@echo "  make server       — run single-player server (uses profile=$(PROFILE))"
	@echo "  make multiserver  — run two-player server   (uses profile=$(PROFILE))"
	@echo "  make client       — run client interactively (uses profile=$(PROFILE))"
	@echo "  make auto-client SID=<student-id>"
	@echo ""
	@echo "Switch profiles per run:    make server PROFILE=lab_server"
	@echo "Point client at a server:   make reconfig NAME=self HOST=<server-ip> PORT=<port>"

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

# --- config --------------------------------------------------------------

# Create $(CONFIG) only when missing — preserves a user-curated file.
# Writes a 'self' entry with this machine's auto-detected LAN IP.
$(CONFIG): | $(STAMP)
	$(PYTHON) src/init_config.py --name self

## config      : ensure $(CONFIG) exists (creates a 'self' profile if missing)
config: $(CONFIG)

## reconfig    : upsert a profile into $(CONFIG). Vars: NAME=<name> HOST=<ip> PORT=<port>
reconfig: $(STAMP)
	$(PYTHON) src/init_config.py \
	    --name $(NAME) \
	    $(if $(HOST),--host $(HOST)) \
	    $(if $(PORT),--port $(PORT))

# --- run ----------------------------------------------------------------

## server      : run the single-player server (PROFILE=<name> to override)
server: $(CONFIG)
	$(PYTHON) src/server.py --profile $(PROFILE)

## multiserver : run the two-player server (PROFILE=<name> to override)
multiserver: $(CONFIG)
	$(PYTHON) src/server_multiuser.py --profile $(PROFILE)

## client      : run the client interactively (PROFILE=<name> to override)
client: $(CONFIG)
	$(PYTHON) src/client.py --profile $(PROFILE)

## auto-client : run the client in --auto mode. Required: SID=<student-id>
auto-client: $(CONFIG)
	@if [ -z "$(SID)" ]; then \
	    echo "Usage: make auto-client SID=<student-id> [PROFILE=<name>]"; exit 2; \
	fi
	$(PYTHON) src/client.py --profile $(PROFILE) --auto --student-id $(SID)

# --- housekeeping -------------------------------------------------------

## clean       : remove Python bytecode caches
clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

## distclean   : clean + remove .venv ($(CONFIG) is user-curated, never auto-deleted)
distclean: clean
	rm -rf $(VENV)
