# TCP Rock-Paper-Scissors Game

Welcome to the TCP Rock-Paper-Scissors game! This is an interactive terminal-based game where you can play classic Rock-Paper-Scissors either against the computer or against another player over the network.

## 🚀 How to Start the Game

Starting the game is incredibly simple. Open your terminal and run this single command:

```bash
make run
```

This will launch an interactive Terminal User Interface (TUI). You can use your **Arrow Keys** (↑ / ↓) and **Enter** to navigate the menus without typing any complicated commands!

### The Main Menu
Once you run the command, you will be presented with a menu:
- **Start Client (Play Game)**: Join a game as a player.
- **Start Server (Single-player)**: Host a PvE game against the computer.
- **Start Server (Multi-player)**: Host a PvP game for two players.
- **Configure Network**: Setup connection details if you are playing across different computers.

---

## 🎮 Game Rules & Modes

You have two different game modes to choose from:

### 1. PvE: Single-Player (Player vs Server)
- **Goal**: Be the first to win **3 rounds**. 
- **Opponent**: You play against the server, which randomly chooses its moves.
- **Rules**: The game will keep going indefinitely until the player successfully wins 3 rounds in total. Ties or server wins do not count towards the end goal. Once you hit 3 wins, the game is over!

### 2. PvP: Multi-Player (Player vs Player)
- **Goal**: Score the most points over exactly **3 rounds**.
- **Opponents**: Exactly two players must connect to the server before the game can begin.
- **Rules**: The game lasts for a strict limit of 3 rounds. 
  - Winning a round gives you **1 point**.
  - A tie gives **0 points** to both players.
  - After the 3 rounds are completed, a final scoreboard is presented to declare the ultimate winner!

---

## 🕹️ How to Play (Step-by-Step UI Guide)

### Step 1: Network Configuration (If playing on different computers)
If you are playing with a friend on a different computer, one of you will be the Server and the other will be the Client.
- On the **Client** machine, select **Configure Network**.
- You can auto-detect a Tailscale IP, your LAN IP, or use **Manual Input** to type in the IP address of the Server machine.

### Step 2: Hosting a Game
On the hosting computer, simply select **Start Server (Single-player)** or **Start Server (Multi-player)**. The server will patiently wait for the required clients to connect.

### Step 3: Joining and Playing
On the player's computer, select **Start Client (Play Game)**.
1. Type in your **Student ID** when prompted.
2. Choose whether you want to play automatically (the computer picks random moves for you) or manually.
3. When a round starts, a prompt will appear. Use your **Arrow Keys** to choose `Rock`, `Paper`, or `Scissors`, and hit **Enter** to lock in your move!
4. Wait for the server to announce the winner of the round.
