"""TCP Rock-Paper-Scissors client (single-client version).

Connects to the server, sends the player's student ID, then plays
rock-paper-scissors until the player wins 3 times.

Usage:
    1. Ask the person running server.py for their LAN IP address.
    2. Set SERVER_HOST to that IP address below.
    3. Start server.py first, then run this script.

    Interactive (default):
        $ python client.py
    Automatic (random valid moves; student ID still required):
        $ python client.py --auto --student-id P76141259
"""

import argparse
import pathlib
import random
import socket
import sys

import questionary
import yaml


# ---------------------------------------------------------------------------
# Configuration — loaded from config/host.yaml (generate via src/init_config.py)
# ---------------------------------------------------------------------------
_CONFIG_PATH = pathlib.Path(__file__).resolve().parent.parent / "config" / "host.yaml"
_DEFAULT_PROFILE = "self"

VALID_MOVES = ("rock", "paper", "scissors")


def _load_profile(name: str) -> tuple[str, int]:
    """Pick `name` out of server_list in config/host.yaml and return (host, port)."""
    if not _CONFIG_PATH.exists():
        sys.exit(
            f"[client] {_CONFIG_PATH} not found. Generate it with:\n"
            "    python src/init_config.py --host <server-ip>\n"
            "or run `make reconfig HOST=<server-ip>` from the project root."
        )
    data = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    profiles = data.get("server_list") or {}
    if name not in profiles:
        available = ", ".join(sorted(profiles)) or "(none)"
        sys.exit(
            f"[client] Profile {name!r} not found in {_CONFIG_PATH}.\n"
            f"         Available: {available}\n"
            f"         Add one with: python src/init_config.py --name {name} --host <server-ip>"
        )
    entry = profiles[name] or {}
    host = str(entry.get("host", "")).strip()
    port = int(entry.get("port", 0))
    if not host or not port:
        sys.exit(f"[client] Profile {name!r} is missing 'host' or 'port'.")
    return host, port


def prompt_move() -> str:
    """Prompt the player for a move via an arrow-key menu.

    Uses questionary for cross-platform ↑/↓ + Enter selection (macOS, Linux,
    and Windows terminals).  Returns a lowercase move name.

    Returns:
        A lowercase string: 'rock', 'paper', or 'scissors'.
    """
    move = questionary.select(
        "Pick a move:",
        choices=list(VALID_MOVES),
    ).ask()
    # .ask() returns None when the user aborts (Ctrl-C / Esc).
    if move is None:
        raise KeyboardInterrupt
    return move


def pick_auto_move() -> str:
    """Pick a random valid move and echo it so auto runs are readable in logs.

    Returns:
        A lowercase string: 'rock', 'paper', or 'scissors'.
    """
    move = random.choice(VALID_MOVES)
    print(f"[Auto] Playing {move}")
    return move


def play_game(sock: socket.socket, student_id: str, auto: bool) -> None:
    """Send the student ID, then loop through game rounds until the game ends.

    After the welcome message the loop:
      1. Picks a move (prompted from the user, or randomly when auto is True).
      2. Sends the move to the server.
      3. Prints the server's response (result + server's move).
      4. Stops when the server sends a 'Game over' message.

    Args:
        sock: An already-connected socket to the server.
        student_id: Username to send as the first message.
        auto: If True, pick moves automatically instead of prompting.
    """
    sock.send(student_id.encode())

    # Receive and display the welcome message
    welcome = sock.recv(1024).decode()
    print(f"[Server] {welcome}\n")

    while True:
        move = pick_auto_move() if auto else prompt_move()
        sock.send(move.encode())

        response = sock.recv(1024).decode()
        print(f"[Server] {response}\n")

        # Server sends "Game over" as the final message
        if response.lower().startswith("game over"):
            break


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TCP Rock-Paper-Scissors client."
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Play automatically with random valid moves (student ID still required).",
    )
    parser.add_argument(
        "--student-id",
        default=None,
        help="Student ID to send as the username. If omitted, you'll be prompted.",
    )
    parser.add_argument(
        "--profile",
        default=_DEFAULT_PROFILE,
        help=f"server_list entry to connect to in config/host.yaml (default: {_DEFAULT_PROFILE!r}).",
    )
    return parser.parse_args()


def main() -> None:
    """Create the client socket, connect to the server, and start the game."""
    args = _parse_args()
    server_host, port = _load_profile(args.profile)

    student_id = args.student_id or input("Enter your student ID: ").strip()
    if not student_id:
        print("[Client] Student ID is required. Exiting.")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print(f"[Client] Connecting to {server_host}:{port} (profile={args.profile!r}) ...")
    try:
        sock.connect((server_host, port))
        print(f"[Client] Connected!\n")
        play_game(sock, student_id, args.auto)
    except ConnectionRefusedError:
        print(
            f"[Client] Could not connect to {server_host}:{port}.\n"
            "  Make sure server.py is running and the IP/port are correct."
        )
    finally:
        sock.close()
        print("[Client] Connection closed.")


if __name__ == "__main__":
    main()