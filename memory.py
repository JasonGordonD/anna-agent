import json
import os

def load_memory(user_id="billy"):
    filename = f"{user_id}.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {
        "trust_level": 5.0,
        "session_count": 1,
        "anxiety_index": 0.3,
        "coke_status": 0
    }

def save_memory(memory, user_id="billy"):
    filename = f"{user_id}.json"
    with open(filename, "w") as f:
        json.dump(memory, f, indent=2)
