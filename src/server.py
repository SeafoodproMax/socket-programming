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

import random
import socket


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
HOST = "192.168.1.10"  # Replace with YOUR machine's LAN IP (not 127.0.0.1)
PORT = 12345
WIN_TARGET = 3         # Client must win this many times to end the game

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
            result_msg = f"Round {round_number}: Server played {server_move} | Client lose"
            server_display = "server win"
        else:
            client_wins += 1
            result_msg = (
                f"Round {round_number}: Server played {server_move} | "
                f"Client win ({client_wins}/{WIN_TARGET})"
            )
            server_display = "server lose"

        print(f"[Server] Round {round_number}: server={server_move}, "
              f"client={client_move} -> {server_display}")
        conn.send(result_msg.encode())

    farewell = f"Game over! {username} won {WIN_TARGET} rounds. GG!"
    conn.send(farewell.encode())
    print(f"[Server] Game ended. {username} reached {WIN_TARGET} wins.")


def main() -> None:
    """Create the server socket, accept one client, and run the game."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow reuse of the port immediately after the process exits
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_sock.bind((HOST, PORT))
    server_sock.listen(1)
    print(f"[Server] Listening on {HOST}:{PORT} ...")

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