# RPG-2D-AGENTIC

A small side-scrolling RPG prototype built with Python and Pygame.

## Explore the world

- **Greenleaf Village** — meet Farmer John and Mira, begin the Slime Trouble quest, and practice on field slimes.
- **Whispering Forest** — follow Ranger Rowan's warning through denser platforms and faster enemies.
- **Slime King's Hollow** — face King Slime and his summoned minions, with battle advice from Scholar Pip.

Walk into the blue portals at map edges to travel. Your level, EXP, quests, health, mana, and inventory persist between areas.

## Run the game

```powershell
python -m pip install -r requirements.txt
python -m src.main
```

Controls:

- `A` / `D`: move
- `Space`: jump and double jump
- `J`: melee attack
- `I`: open/close inventory
- `Q/W/E/R`: equip sword, helmet, shirt, or pants while inventory is open
- `1/2/3/4`: spend available stat points on STR/DEX/INT/LUK while inventory is open
- `K`: Fireball
- `L`: Ice Bolt
- `Left Shift`: dash
- `1` / `2`: use health or mana potion
- `E`: interact with NPCs

## Run tests

The gameplay tests use SDL's headless drivers and do not open a game window.

```powershell
python -m unittest discover -s tests -v
```
