"""TCP Rock-Paper-Scissors server (single-client version).

Waits for one client to connect, plays rock-paper-scissors until the
client wins 3 times, then closes the connection.

Usage:
    1. Run `ipconfig` (Windows) or `ifconfig` (Mac/Linux) to find your LAN IP.
    2. Set HOST to that IP address below.
    3. Start this script before launching client.py.

Typical session::

    $ python server.py
    [Server] Listening on 192.168.1.10:12345 ...
    [Server] P76141259 connected from ('192.168.1.20', 54321)
    ...
"""

import argparse
import pathlib
import random
import socket
import sys

import yaml


# ---------------------------------------------------------------------------
# Configuration — loaded from config/host.yaml (generate via src/init_config.py)
# ---------------------------------------------------------------------------
_CONFIG_PATH = pathlib.Path(__file__).resolve().parent.parent / "config" / "host.yaml"
_DEFAULT_PROFILE = "self"

WIN_TARGET = 3         # Client must win this many times to end the game


def _load_profile(name: str) -> tuple[str, int]:
    """Pick `name` out of server_list in config/host.yaml and return (host, port)."""
    if not _CONFIG_PATH.exists():
        sys.exit(
            f"[server] {_CONFIG_PATH} not found. Generate it with:\n"
            "    python src/init_config.py\n"
            "or run `make` from the project root."
        )
    data = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    profiles = data.get("server_list") or {}
    if name not in profiles:
        available = ", ".join(sorted(profiles)) or "(none)"
        sys.exit(
            f"[server] Profile {name!r} not found in {_CONFIG_PATH}.\n"
            f"         Available: {available}\n"
            f"         Add one with: python src/init_config.py --name {name}"
        )
    entry = profiles[name] or {}
    host = str(entry.get("host", "")).strip()
    port = int(entry.get("port", 0))
    if not host or not port:
        sys.exit(f"[server] Profile {name!r} is missing 'host' or 'port'.")
    return host, port

# Valid moves and the move that beats each key
BEATS = {
    "rock": "scissors",
    "paper": "rock",
    "scissors": "paper",
}


def determine_outcome(server_move: str, client_move: str) -> str:
    """Return the round result from the server's perspective.

    Args:
        server_move: The move chosen by the server ('rock', 'paper', or
            'scissors').
        client_move: The move sent by the client.

    Returns:
        One of 'server_win', 'client_win', or 'draw'.
    """
    if server_move == client_move:
        return "draw"
    if BEATS[server_move] == client_move:
        return "server_win"
    return "client_win"


def play_game(conn: socket.socket, username: str) -> None:
    """Run the full rock-paper-scissors game loop with one connected client.

    Sends a welcome message, then loops round-by-round until the client
    accumulates WIN_TARGET wins.  Each round:
      - Waits for the client's move.
      - Picks a random server move.
      - Sends the result back.

    Args:
        conn: The connected client socket returned by accept().
        username: The student ID / username sent by the client on login.
    """
    conn.send(f"Welcome Game {username}".encode())

    client_wins = 0
    server_wins = 0
    round_number = 0

    while client_wins < WIN_TARGET:
        raw = conn.recv(1024).decode().strip().lower()
        if not raw:
            print("[Server] Client disconnected unexpectedly.")
            break

        if raw not in BEATS:
            conn.send("Invalid move. Please send rock, paper, or scissors.".encode())
            continue

        round_number += 1
        client_move = raw
        server_move = random.choice(list(BEATS.keys()))
        outcome = determine_outcome(server_move, client_move)

        if outcome == "draw":
            result_msg = f"Round {round_number}: Server played {server_move} | Draw"
            server_display = "draw"
        elif outcome == "server_win":
            server_wins += 1
            result_msg = f"Round {round_number}: Server played {server_move} | Client lose"
            server_display = "server win"
        else:
            client_wins += 1
            # End immediately on the winning round so client.py can stop
            # without requiring an extra send/recv cycle.
            if client_wins == WIN_TARGET:
                result_msg = (
                    f"Game over! Round {round_number}: Server played {server_move} | "
                    f"Client win ({client_wins}/{WIN_TARGET}). GG!"
                )
                print(
                    f"[Server] Round {round_number}: server={server_move}, "
                    f"client={client_move} -> server lose"
                )
                conn.send(result_msg.encode())
                print(
                    f"[Server] Game ended. {username} reached {WIN_TARGET} wins. "
                    f"(server wins: {server_wins})"
                )
                return

            result_msg = (
                f"Round {round_number}: Server played {server_move} | "
                f"Client win ({client_wins}/{WIN_TARGET})"
            )
            server_display = "server lose"

        print(f"[Server] Round {round_number}: server={server_move}, "
              f"client={client_move} -> {server_display}")
        conn.send(result_msg.encode())



def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TCP Rock-Paper-Scissors server (single-client).",
    )
    parser.add_argument(
        "--profile",
        default=_DEFAULT_PROFILE,
        help=f"server_list entry to bind to in config/host.yaml (default: {_DEFAULT_PROFILE!r}).",
    )
    return parser.parse_args()


def main() -> None:
    """Create the server socket, accept one client, and run the game."""
    args = _parse_args()
    host, port = _load_profile(args.profile)

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow reuse of the port immediately after the process exits
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_sock.bind((host, port))
    server_sock.listen(1)
    print(f"[Server] Listening on {host}:{port} (profile={args.profile!r}) ...")

    conn, addr = server_sock.accept()
    print(f"[Server] Client connected from {addr}")

    try:
        # First message from client is the username / student ID
        username = conn.recv(1024).decode().strip()
        if not username:
            print("[Server] No username received. Closing.")
            return
        print(f"[Server] {username} connected from {addr}")
        play_game(conn, username)
    finally:
        conn.close()
        server_sock.close()
        print("[Server] Connection closed.")


if __name__ == "__main__":
    main()