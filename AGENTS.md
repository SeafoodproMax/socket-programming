# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project context

NCKU 2026 Spring *Computer Networks* homework: a TCP rock-paper-scissors game written with Python's `socket` standard library. The full assignment spec is in `references/Socket-Programming_HW.md` (Traditional Chinese) — read it before changing game behavior, as the grading rubric pins down specific rules.

Hard constraints from the spec that directly shape the code:

- **Flask and similar web frameworks are forbidden** (spec §二.2). The intent of the ban is web-framework abstractions that would skip the manual IP-setup step. Client-only TUI helpers like `questionary` (used by `client.py` for the arrow-key move picker) are therefore fine; the servers remain stdlib-only. Keep any new dependencies client-side and mention them in the report.
- TCP only (`socket.SOCK_STREAM`).
- `127.0.0.1` is disallowed — the grader gives zero if used. `HOST` / `SERVER_HOST` must be edited to the machine's real LAN IP before running. This is why the defaults look like `192.168.1.10` rather than loopback.
- Deliverable filenames are fixed: `client.py`, `server.py`, `server_multiuser.py`. Do not rename.
- Single-player: the **client** must win **3 times** (not 3 rounds) to end the game. Draws and server wins do not terminate.
- Multi-player: exactly **3 rounds**, win-per-round scoring. Spec note: if three players were ever added and ties occurred (e.g. 2× scissors + 1× paper), everyone in the majority gets 1 point, minority gets 0. Current two-player implementation simplifies this to "winner +1, draw = both 0".
- Single-player client must send the **real student ID** as its username. Multi-player usernames can be anything.

## Running the code

After `git pull`, one command bootstraps everything:

```bash
make                     # creates .venv, installs deps, ensures config/host.yaml exists
make server              # OR: multiserver | client | auto-client SID=<id>
```

Switch profiles per run without editing anything:

```bash
make server PROFILE=lab_server
make client PROFILE=localhost
```

On a client machine pointing at a different server, upsert a profile first:

```bash
make reconfig NAME=self HOST=<server-ip> PORT=<port>
make client PROFILE=self
```

Both machines still need their firewalls down and must share a LAN / hotspot. The `make reconfig` defaults (`NAME=$(PROFILE)` = `self`) match the default `--profile self` used by all three deliverables.

There are no tests, no linter config, and no build step.

### Config file: `config/host.yaml`

This file is **version-controlled** (not gitignored) because it holds the set of known-good profiles — `lab_server`, `localhost`, and whatever else gets curated over time. Shape:

```yaml
server_list:
  <profile>:
    host: "<ip>"
    port: <int>
```

`src/init_config.py` upserts ONE entry (by `--name`, default `self`) while preserving all other entries — safe to re-run. The three deliverables each inline a small `_load_profile(name)` helper that picks `server_list[name]`; they fail loudly listing available profiles when a missing name is passed. No shared `config.py` module exists on purpose: each of `client.py` / `server.py` / `server_multiuser.py` stays self-contained so the required-files zip in §六 still runs standalone.

## Architecture

Three scripts, one shared wire protocol. All messages are plain UTF-8 text, one logical message per `send()`, read with `recv(1024)`. No length prefixing or delimiters — the code relies on each `send` landing in its own `recv`, which is fragile but acceptable for this assignment's traffic pattern.

**Protocol (applies to both servers):**

1. Client's first `send()` is the username/student ID.
2. Server replies with `"Welcome Game <username>"` — this exact prefix is required by the rubric.
3. Per-round: client sends a lowercase move (`rock` / `paper` / `scissors`); server replies with a human-readable result line. Invalid moves get `"Invalid move. Please send rock, paper, or scissors."` and the round is retried.
4. Termination differs between the two servers (see below).

**`src/server.py` (single-client).** Accepts one connection, runs `play_game` inline. Loops until `client_wins == WIN_TARGET` (3). Server's move is `random.choice`. Final message begins with `"Game over!"` — `client.py` detects termination by checking `response.lower().startswith("game over")`.

**`src/server_multiuser.py` (two-client).** Accepts exactly two connections in `main`, spawns one thread per client via `handle_client`. Synchronization uses a shared `threading.Barrier(2)` plus a few mutable "cells" (`round_results = [None]`, `player_names = [None, None]`) and a `_moves` dict guarded by `_moves_lock`. The coordination pattern per round is three barrier waits:

1. `barrier.wait()` after both clients submit their move → both moves are now in `_moves`.
2. Only `player_slot == 0` judges the round and writes `round_results[0]` + updates `_scores` — this avoids a double-count race.
3. `barrier.wait()` again → both threads now safely read `round_results[0]` and `send()` it to their client.

After 3 rounds, one final `barrier.wait()` fences the scoreboard construction, then each thread sends the scoreboard to its own client. Fixed number of rounds — do not port the single-player "first to N wins" termination here; the spec requires exactly 3 rounds.

**`src/client.py`.** Shared by both servers. After sending the username and printing the welcome, it loops `prompt_move` → `send` → `recv` → `print`, breaking when the server response starts with `"game over"`. Note: this termination check was written for the single-player server; the multi-user server's final message is a scoreboard beginning with `=== Final Scoreboard ===`, and there's also an extra `"Both players connected!..."` message sent before round 1 that the current client treats as if it were a round result. Keep this in mind when touching either side — changing one protocol message likely requires changing the client's message-handling loop too.

## Memory

Persistent memory for this project lives under `memory/` (see `MEMORY.md` index). Prefer updating existing entries over adding new ones.

## Style
- Follow Google's Python style guide (https://google.github.io/styleguide/pyguide.html) where possible, but prioritize clarity and correctness over strict adherence. The code is intentionally simple and straightforward to match the assignment's educational goals.
- Use descriptive variable and function names. Avoid abbreviations unless they are widely understood (e.g. `recv` is fine, but `r` is not).
- Add comments to explain non-obvious logic, especially around the synchronization in `server_multiuser.py`. The code is simple enough that excessive commenting is not needed, but key steps in the protocol and thread coordination should be documented.