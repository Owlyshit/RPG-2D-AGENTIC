import json
import os

SAVE_FILE = "high_scores.json"

def load_high_scores():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                return data.get("high_score", 0)
        except json.JSONDecodeError:
            print(f"Warning: {SAVE_FILE} is corrupted. Starting with no high score.")
            return 0
    return 0

def save_high_scores(score):
    data = {"high_score": score}
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)
    print(f"High score saved: {score}")
