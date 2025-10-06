import json
import os

def load_memory(user_id='billy'):
    filename = f"memory_{user_id}.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    default_memory = {
        "trust_level": 5.0,
        "session_count": 1,
        "anxiety_index": 0.3,
        "coke_status": 0,
        "user_id": user_id  # Ensure default includes user_id
    }
    return default_memory

def save_memory(memory, user_id='billy'):
    memory['user_id'] = user_id  # Ensure user_id in blob for Supabase
    filename = f"memory_{user_id}.json"
    with open(filename, "w") as f:
        json.dump(memory, f, indent=2)
