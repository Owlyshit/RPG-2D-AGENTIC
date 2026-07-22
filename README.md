# RPG-2D-AGENTIC

A small side-scrolling RPG prototype built with Python and Pygame.

## Run the game

```powershell
python -m pip install -r requirements.txt
python -m src.main
```

Controls:

- `A` / `D`: move
- `Space`: jump and double jump
- `J`: melee attack
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
