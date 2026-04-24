"""TCP Rock-Paper-Scissors client (single-client version).

Connects to the server, sends the player's student ID, then plays
rock-paper-scissors until the player wins 3 times.

Usage:
    1. Ask the person running server.py for their LAN IP address.
    2. Set SERVER_HOST to that IP address below.
    3. Start server.py first, then run this script.

Typical session::

    $ python client.py
    Enter your student ID: P76141259
    [Client] Connecting to 192.168.1.10:12345 ...
    [Server] Welcome Game P76141259
    Your move (rock/paper/scissors): rock
    [Server] Round 1: Server played scissors | Client win (1/3)
    ...
"""

import socket


# ---------------------------------------------------------------------------
# Configuration — must match server.py
# ---------------------------------------------------------------------------
SERVER_HOST = "192.168.1.10"  # Replace with the SERVER machine's LAN IP
PORT = 12345

VALID_MOVES = {"rock", "paper", "scissors"}


def prompt_move() -> str:
    """Prompt the player for a valid move, looping until one is given.

    Returns:
        A lowercase string: 'rock', 'paper', or 'scissors'.
    """
    while True:
        move = input("Your move (rock / paper / scissors): ").strip().lower()
        if move in VALID_MOVES:
            return move
        print(f"  Invalid input '{move}'. Please type rock, paper, or scissors.")


def play_game(sock: socket.socket) -> None:
    """Send the student ID, then loop through game rounds until the game ends.

    After the welcome message the loop:
      1. Prompts the player for a move.
      2. Sends the move to the server.
      3. Prints the server's response (result + server's move).
      4. Stops when the server sends a 'Game over' message.

    Args:
        sock: An already-connected socket to the server.
    """
    student_id = input("Enter your student ID: ").strip()
    sock.send(student_id.encode())

    # Receive and display the welcome message
    welcome = sock.recv(1024).decode()
    print(f"[Server] {welcome}\n")

    while True:
        move = prompt_move()
        sock.send(move.encode())

        response = sock.recv(1024).decode()
        print(f"[Server] {response}\n")

        # Server sends "Game over" as the final message
        if response.lower().startswith("game over"):
            break


def main() -> None:
    """Create the client socket, connect to the server, and start the game."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print(f"[Client] Connecting to {SERVER_HOST}:{PORT} ...")
    try:
        sock.connect((SERVER_HOST, PORT))
        print(f"[Client] Connected!\n")
        play_game(sock)
    except ConnectionRefusedError:
        print(
            f"[Client] Could not connect to {SERVER_HOST}:{PORT}.\n"
            "  Make sure server.py is running and the IP/port are correct."
        )
    finally:
        sock.close()
        print("[Client] Connection closed.")


if __name__ == "__main__":
    main()