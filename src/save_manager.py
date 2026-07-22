import json
from pathlib import Path


SAVE_VERSION = 1
DEFAULT_SAVE_FILE = Path("savegame.json")


def save_game(state, save_file=DEFAULT_SAVE_FILE):
    """Persist a versioned game state with an atomic file replacement."""
    path = Path(save_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    payload = {"version": SAVE_VERSION, "state": state}
    temporary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary_path.replace(path)


def load_game(save_file=DEFAULT_SAVE_FILE):
    """Return a saved state, or None when the file is missing/invalid."""
    path = Path(save_file)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("version") != SAVE_VERSION or not isinstance(payload.get("state"), dict):
        return None
    return payload["state"]
