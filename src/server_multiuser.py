"""TCP Rock-Paper-Scissors server (two-player version).

Waits for exactly two clients to connect (using one thread per client),
then plays a best-of-3 match between them.  After all 3 rounds the server
sends a scoreboard to both clients and closes the connections.

Usage:
    1. Set HOST to your LAN IP address (not 127.0.0.1).
    2. Start this script before launching client.py on either machine.
    3. Both clients must connect before the game begins.

Typical session::

    $ python server_multiuser.py
    [Server] Listening on 192.168.1.10:12345 ...
    [Server] Player 1 connected: P76141259 from ('192.168.1.20', 54321)
    [Server] Player 2 connected: P76141260 from ('192.168.1.21', 54322)
    [Server] Both players connected. Starting game!
    ...
"""

import socket
import threading


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
HOST = "192.168.1.10"  # Replace with YOUR machine's LAN IP (not 127.0.0.1)
PORT = 12345
TOTAL_ROUNDS = 3

BEATS = {
    "rock": "scissors",
    "paper": "rock",
    "scissors": "paper",
}

# Shared state — protected by a threading.Barrier and a threading.Lock
# so the two client threads can synchronise each round safely.
_moves: dict[str, str] = {}       # { username: move } filled each round
_scores: dict[str, int] = {}      # { username: wins }
_moves_lock = threading.Lock()


def _recv_move(conn: socket.socket, username: str) -> str:
    """Block until a valid move is received from the given client.

    Keeps prompting (via the socket) until the client sends 'rock',
    'paper', or 'scissors'.

    Args:
        conn: The connected client socket.
        username: Used only for server-side logging.

    Returns:
        A validated lowercase move string.
    """
    while True:
        raw = conn.recv(1024).decode().strip().lower()
        if raw in BEATS:
            return raw
        conn.send("Invalid move. Please send rock, paper, or scissors.".encode())
        print(f"[Server] Invalid move from {username}: '{raw}'")


def _determine_outcome(move_a: str, move_b: str) -> str:
    """Compare two moves and return who won.

    Args:
        move_a: Move from player A.
        move_b: Move from player B.

    Returns:
        'a_win', 'b_win', or 'draw'.
    """
    if move_a == move_b:
        return "draw"
    if BEATS[move_a] == move_b:
        return "a_win"
    return "b_win"


def handle_client(
    conn: socket.socket,
    addr: tuple,
    player_slot: int,
    barrier: threading.Barrier,
    round_results: list,
    player_names: list,
) -> None:
    """Manage communication with one player for the full game.

    This function runs in its own thread.  It:
      1. Receives the username and sends a welcome message.
      2. Waits at the barrier until the other player is also ready.
      3. Loops TOTAL_ROUNDS times:
           a. Collects the player's move.
           b. Waits at the barrier so both moves arrive before judging.
           c. (Player-slot-0 thread only) judges the round and stores result.
           d. Waits at the barrier so the result is ready before sending.
           e. Sends the round result to the client.
      4. Sends the final scoreboard.

    Args:
        conn: The connected client socket.
        addr: The client's (ip, port) tuple, used for logging.
        player_slot: 0 for the first player, 1 for the second.
        barrier: A threading.Barrier(2) shared between the two player threads.
        round_results: A list of length 1 used as a mutable result cell so
            the slot-0 thread can share the judged result with the slot-1
            thread.  Pre-populated with [None].
        player_names: A list of length 2 pre-populated with [None, None];
            each thread writes its own username so both threads can access
            both names for the scoreboard.
    """
    try:
        # --- Login ---
        username = conn.recv(1024).decode().strip()
        if not username:
            print(f"[Server] No username from {addr}. Disconnecting.")
            return

        player_names[player_slot] = username
        _scores[username] = 0
        print(f"[Server] Player {player_slot + 1} connected: {username} from {addr}")

        conn.send(f"Welcome Game {username}".encode())

        # Wait until both players have sent their usernames
        barrier.wait()

        if player_slot == 0:
            print("[Server] Both players connected. Starting game!")

        conn.send("Both players connected! Game starting now.".encode())

        # --- Game loop ---
        for round_num in range(1, TOTAL_ROUNDS + 1):
            conn.send(f"Round {round_num}/{TOTAL_ROUNDS} — send your move:".encode())

            move = _recv_move(conn, username)

            with _moves_lock:
                _moves[username] = move

            # Wait until both players have submitted their move
            barrier.wait()

            # Only one thread judges to avoid a race condition
            if player_slot == 0:
                name_a = player_names[0]
                name_b = player_names[1]
                move_a = _moves[name_a]
                move_b = _moves[name_b]
                outcome = _determine_outcome(move_a, move_b)

                if outcome == "draw":
                    result_text = (
                        f"Round {round_num}: {name_a} played {move_a} vs "
                        f"{name_b} played {move_b} — Draw (no points)"
                    )
                elif outcome == "a_win":
                    _scores[name_a] += 1
                    result_text = (
                        f"Round {round_num}: {name_a} played {move_a} vs "
                        f"{name_b} played {move_b} — {name_a} wins the round!"
                    )
                else:
                    _scores[name_b] += 1
                    result_text = (
                        f"Round {round_num}: {name_a} played {move_a} vs "
                        f"{name_b} played {move_b} — {name_b} wins the round!"
                    )

                round_results[0] = result_text
                print(f"[Server] {result_text}")

            # Wait until the result string is written before both threads read it
            barrier.wait()

            conn.send(round_results[0].encode())

        # --- Final scoreboard ---
        barrier.wait()  # Ensure all rounds are complete before building board

        name_a = player_names[0]
        name_b = player_names[1]
        score_a = _scores[name_a]
        score_b = _scores[name_b]

        if score_a > score_b:
            winner_line = f"Winner: {name_a}!"
        elif score_b > score_a:
            winner_line = f"Winner: {name_b}!"
        else:
            winner_line = "It's a tie!"

        scoreboard = (
            f"\n=== Final Scoreboard ===\n"
            f"  {name_a}: {score_a} win(s)\n"
            f"  {name_b}: {score_b} win(s)\n"
            f"{winner_line}\n"
            f"========================"
        )
        conn.send(scoreboard.encode())
        print(f"[Server] Sent scoreboard to {username}.")

    finally:
        conn.close()


def main() -> None:
    """Accept exactly two clients, then launch a handler thread for each."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(2)
    print(f"[Server] Listening on {HOST}:{PORT} ...")

    # Shared structures passed to both threads
    barrier = threading.Barrier(2)
    round_results = [None]   # Mutable cell: slot-0 thread writes, both read
    player_names = [None, None]

    connections = []
    for slot in range(2):
        conn, addr = server_sock.accept()
        connections.append((conn, addr, slot))
        print(f"[Server] Accepted connection {slot + 1}/2 from {addr}")

    threads = []
    for conn, addr, slot in connections:
        t = threading.Thread(
            target=handle_client,
            args=(conn, addr, slot, barrier, round_results, player_names),
            daemon=True,
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    server_sock.close()
    print("[Server] All done. Server closed.")


if __name__ == "__main__":
    main()