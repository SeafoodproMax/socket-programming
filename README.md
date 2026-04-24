# TCP Rock-Paper-Scissors

NCKU 2026 Spring, *Computer Networks* — Socket Programming homework.

A TCP rock-paper-scissors game with two server flavors (single-client first-to-3-wins and two-client best-of-3) and one shared client. Host/port are read from a per-machine `config/host.yaml`; no editing of the Python files is needed.

Full assignment spec: [`references/Socket-Programming_HW.md`](references/Socket-Programming_HW.md).

## Requirements

- Python 3.10+ (tested on 3.14)
- Two machines on the same LAN / hotspot (spec forbids `127.0.0.1`)
- Firewalls disabled on both machines for the chosen port

## Quick start

```bash
git clone <this repo>
cd SocketProgramming
make                          # creates .venv, installs deps, upserts 'self' profile
```

After that, on the **server machine**:

```bash
make server                   # single-player (first-to-3-wins)
# or
make multiserver              # two-player (best-of-3)
```

On each **client machine**, first point `self` at the server's IP, then run:

```bash
make reconfig HOST=<server-ip> PORT=<server-port>
make client                   # interactive play with arrow-key move picker
```

That's it — no file edits required between machines.

## Config file — `config/host.yaml`

Named profiles live under `server_list`. Each profile holds one `host` + `port`. The file is version-controlled so you can curate a few useful entries once and reuse them.

```yaml
server_list:
  self:
    host: 10.9.210.33     # auto-filled by `make reconfig` / init_config.py
    port: 12345
  lab_server:
    host: 10.7.209.196
    port: 9999
  localhost:
    host: 127.0.0.1       # for local debugging only; NOT acceptable for grading
    port: 8080
```

Pick which profile a command uses with `PROFILE=<name>`:

```bash
make server PROFILE=lab_server
make client PROFILE=lab_server
```

Default profile is `self`, which `make reconfig` upserts — `lab_server` / `localhost` / anything else you add is preserved.

### Managing profiles

```bash
# Auto-detect this machine's LAN IP and write it to the 'self' profile.
make config

# Add or update a named profile explicitly.
make reconfig NAME=home HOST=192.168.1.50 PORT=12345

# Same thing without make:
python src/init_config.py --name home --host 192.168.1.50 --port 12345
```

`init_config.py` is always an upsert — it touches exactly one entry and leaves the rest of `server_list` alone.

## Client modes

Interactive (default):

```bash
make client
```

You'll be prompted for your student ID, then an arrow-key menu (↑ / ↓ / Enter) selects rock / paper / scissors each round.

Automatic (random valid moves — still sends your student ID):

```bash
make client AUTO=1 SID=P76141259
# equivalent:
make auto-client SID=P76141259
```

Useful for load-testing the multi-player server with two clients on one machine.

## Make targets

| Target | What it does |
|---|---|
| `make` / `make all` | venv + deps + ensure `config/host.yaml` exists + print next steps |
| `make install` | Create `.venv`, install `requirements.txt` |
| `make config` | Ensure `config/host.yaml` exists (writes `self` if missing) |
| `make reconfig NAME=.. HOST=.. PORT=..` | Upsert a profile |
| `make server [PROFILE=..]` | Start single-player server |
| `make multiserver [PROFILE=..]` | Start two-player server |
| `make client [PROFILE=..] [AUTO=1 SID=..]` | Start client |
| `make auto-client SID=..` | Alias for `make client AUTO=1 SID=..` |
| `make clean` | Remove `__pycache__` / `.pyc` |
| `make distclean` | `clean` + remove `.venv` (keeps `config/host.yaml`) |
| `make help` | List targets with one-line descriptions |

## How the two game modes behave

**Single-player (`server.py`):** server picks random moves. Game ends when the client wins 3 rounds total — the winning round itself carries the `Game over!` prefix, so there's no separate farewell message. Server logs its own wins / losses for symmetry.

**Two-player (`server_multiuser.py`):** accepts exactly two clients, plays 3 rounds. Per-round scoring: winner +1, draw = both 0. Scoreboard sent to both clients at the end. Synchronization is via a `threading.Barrier(2)` shared between the two handler threads.

The shared `client.py` works with both servers — it auto-detects multi-player pre-round prompts via a short receive timeout and relays them to you before asking for your next move.

## Project layout

```
.
├── Makefile
├── README.md
├── requirements.txt          # questionary (client TUI) + pyyaml (config)
├── config/
│   └── host.yaml             # server_list of named profiles — version-controlled
├── references/
│   └── Socket-Programming_HW.md
└── src/
    ├── client.py
    ├── server.py             # single-client server
    ├── server_multiuser.py   # two-client server
    └── init_config.py        # upserts one profile into config/host.yaml
```

## Notes for the homework report

Per §六 of the spec, the submission zip must contain **`client.py`**, **`server.py`**, **`server_multiuser.py`**, and your PDF report. Because the code imports `questionary` / `pyyaml` and reads `config/host.yaml`, also include in your zip:

- `requirements.txt` + setup note (`pip install -r requirements.txt`)
- `config/host.yaml` (or mention running `python src/init_config.py` after unzip)
- `src/init_config.py`

For the report screenshots, run the **interactive** client (`make client`) — that's what shows the `Welcome Game <student-id>` prompt and the arrow-key move picker clearly.

Required IP proof: screenshots of `ipconfig` / `ifconfig` on both machines showing their LAN IPs. Using `127.0.0.1` is a zero-score per §七.
