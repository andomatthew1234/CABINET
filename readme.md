# 🕹️ THE CABINET

THE CABINET is a games launcher with 2D retro games that work offline. Its lightweight, fun to play, and works offline.

## 🎮 Games so far
* **StreetFight** Classic street fighter with pro physics. Fight AI with special moves.
* **NEONRACE** High speed arcade traffic dodging. Survive the highway.
* **Snake** Control the snake to eat food - and avoid the rocks!
* **StreetFight** Classic street fighter with pro physics. Fight AI with special moves.
* **Tetris** Classic retro block game - test your block placing!
* **Water Sort** Sort the bottles. Randomly generated, infinite levels, how many can you get through?
* **Pong** A retro game 'pong' where you essentially play ping pong with arrow keys. It comes with SO MANY LEVELS, including:
    * **🏓 BitGame** Premium feel, classic functionality.
    * **👾 Classic** A more 'classic' theme.
    * **❄️ Snowball** Grey/white 'snowy' theme. Comes with bonus: hover over the dot press the 'z' key to unlock 5 bonus points.
    * **🌐 XDISTOPIA** Dystopian 'hacker' vibe theme.
    * **⌛ Time Attack** How many can you get in 30s?
    * **⏱️ ACCELERATION** Standard, but the ball goes faster at a 5X RATE! How fast can you go?
    * **🔒 [COLLISIONBREAK]** LOCKED gamemode, get 100 points to unlock and see the fun!
* **Interactive Hover Effects:**
* **System Tools:** Integrated system update module for seamless updates.
## ℹ️ Features
* **One-click update** Automatically updates the launcher and all games for you in one click. Easy!
* **Soundtrack** Every game has an anthem to it - listen along!
* **Stunning launcher** hover effects, easy use, auto-game import.

## 🎱 Let's get started.
Instructions for getting started are coming soon, stay tuned!

## ⏬ Custom game intergrations
* **Devs,** import your own games EASILY with the cabinet launcher. Just drag and drop your game into the /games/ folder with this structure:
/
├── app.py           # Main launcher application
├── install.bat      # Installation script
├── LICENCES.MD      # License information
├── readme.md        # This file
├── /games/          # Folder that stores all games
│   ├──| **your_game_folder_here**/     <- drag and drop your games folder here.
|   |  ├── **game_files (see below)**
│   └── ...
├── /music/          # Audio files (menu, launch, exit)
└── /other/          # System tools, update, runner.
🤔 What do I put in my game files folder?
- THE CABINET uses pygame - and so should your game. It should contain 'config.json', and 'game.py'.
game.py:
This is the game itself. It should use Pygame-ce.
config.json:
This tells the launcher what to expect, your highscores, and more. An example:
{
    "title": "game_name",
    "description": "game_description",
    "high_score": 0
}
*NOTE: you can choose not to incorporate high_score, but we recomend it for the launcher.*