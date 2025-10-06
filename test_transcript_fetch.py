import requests
import json
from subprocess import run, PIPE

# Unrestricted key for full scopes
KEY = "sk_395144d7d8604f470abb8d983081770c371c3011e03962e7"
BASE_URL = "https://api.elevenlabs.io/v1"
HEADERS = {"xi-api-key": KEY, "Content-Type": "application/json"}

agent_id = "agent_2901k6qjvk71e9cbftde9wzyt94n"

# Step 1: ConvAI metadata (baseline)
try:
    resp = requests.get(f"{BASE_URL}/convai/conversations", headers=HEADERS)
    resp.raise_for_status()
    convos = resp.json()
    print(f"ConvAI Metadata: {len(convos)} conversations.")
    if convos:
        conv_id = convos[0]['id']  # First ID
        print(f"Test Conv ID: {conv_id}")
except Exception as e:
    print(f"Metadata fail: {e}")
    conv_id = None

# Step 2: Transcript fetch (post-UI toggle)
if conv_id:
    try:
        transcript_url = f"{BASE_URL}/agents/{agent_id}/conversations/{conv_id}/transcript"
        resp = requests.get(transcript_url, headers=HEADERS)
        if resp.status_code == 200:
            transcript = resp.json()
            print("Transcript Success:")
            print(json.dumps(transcript, indent=2))  # Turns array
            with open(f"transcript_{conv_id}.json", "w") as f:
                json.dump(transcript, f)
            print("Saved to transcript_{conv_id}.json")
        else:
            print(f"Transcript {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Fetch fail: {e}")
