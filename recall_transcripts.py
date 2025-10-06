# recall_transcripts.py — Retrieve and store conversation transcripts from ElevenLabs Agents Platform

import requests, json, time
from datetime import datetime
from pathlib import Path

# === CONFIGURATION ===
# replace the strings below with your test key and agent ID exactly as written
ELEVENLABS_API_KEY = "sk_68d5538cba995e9bc5a318fc1b344a5fa8c2e2d557ae4019"
AGENT_ID = "agent_2901k6qjvk71e9cbftde9wzyt94n"

BASE_URL = "https://api.elevenlabs.io/v1"
CONVERSATIONS_ENDPOINT = f"{BASE_URL}/agents/{AGENT_ID}/conversations"
TRANSCRIPT_ENDPOINT = f"{BASE_URL}/agents/{AGENT_ID}/conversations/{{id}}/transcript"
OUTPUT_DIR = Path("transcripts")
HEADERS = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}

def fetch_conversations():
    r = requests.get(CONVERSATIONS_ENDPOINT, headers=HEADERS, timeout=10)
    if r.status_code != 200:
        print("❌", r.status_code, r.text)
        return []
    return r.json().get("conversations", [])

def fetch_transcript(conv_id):
    r = requests.get(TRANSCRIPT_ENDPOINT.format(id=conv_id), headers=HEADERS, timeout=10)
    if r.status_code != 200:
        print("⚠️", r.status_code, r.text)
        return None
    return r.json().get("text", "")

def save_transcript(conv_id, text):
    OUTPUT_DIR.mkdir(exist_ok=True)
    fn = OUTPUT_DIR / f"conversation_{conv_id}.txt"
    with open(fn, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ Saved transcript: {fn}")

if __name__ == "__main__":
    print(f"🎧 Using agent {AGENT_ID}")
    conversations = fetch_conversations()
    if not conversations:
        print("⚠️ No conversations found or API key lacks Agents scope.")
    for c in conversations:
        cid = c.get("id")
        print("Pulling", cid)
        txt = fetch_transcript(cid)
        if txt:
            save_transcript(cid, txt)
        time.sleep(2)
    print("🎯 Done")
