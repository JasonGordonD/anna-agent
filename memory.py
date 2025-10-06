import json
import os

def load_memory(user_id='billy'):
    """
    Load persona-specific memory file. Each user_id has its own persistent memory blob.
    Fallback initializes baseline trust/anxiety/edge levels.
    """
    filename = f"memory_{user_id}.json"
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[memory] Warning: Failed to parse {filename}: {e}")
            pass

    # Default baseline if no file exists
    default_memory = {
        "user_id": user_id,
        "trust_level": 5.0,
        "anxiety_index": 0.3,
        "edge_index": 0.5,
        "coke_status": 0,
        "session_count": 0
    }
    print(f"[memory] Initialized new memory for {user_id}")
    return default_memory


def save_memory(memory, user_id='billy'):
    """
    Save persona-specific memory file to disk.
    Ensures user_id is embedded for Supabase logs.
    """
    memory["user_id"] = user_id
    filename = f"memory_{user_id}.json"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2)
        print(f"[memory] Saved memory to {filename}")
    except Exception as e:
        print(f"[memory] Error saving memory for {user_id}: {e}")
