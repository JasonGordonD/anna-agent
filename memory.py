import json

def load_memory(user_id="billy"):
    try:
        with open(f"{user_id}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "trust_level": 5.5,
            "session_count": 1,
            "anxiety_index": 0.3,
            "coke_status": 0
        }

def save_memory(data, user_id="billy"):
    with open(f"{user_id}.json", "w") as f:
        json.dump(data, f, indent=2)
