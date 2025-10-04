# transcript_processor.py — Fully Dynamic Schema-Driven Memory Scorer

import requests
import json
from datetime import datetime
from schema_loader import load_schema

# === HARD-CODED TEST KEYS ===
ELEVENLABS_API_KEY = "545d74e3e46e500a2cf07fdef11338abf4ccf428738d17b9b8d6fa295963c4ed"
SUPABASE_URL = "https://qumhcrbukjhfwcsoxpyr.supabase.co/rest/v1/session_logs"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0.EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI"

TRANSCRIPT_LIST_API = "https://api.elevenlabs.io/v1/recordings"
TRANSCRIPT_BODY_API = "https://api.elevenlabs.io/v1/recordings/{id}/transcript"

HEADERS = {
    "xi-api-key": ELEVENLABS_API_KEY,
    "Content-Type": "application/json"
}

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

schema = load_schema()

# === CORE FUNCTIONS ===

def fetch_latest_transcript():
    print("🔍 Fetching transcript IDs...")
    res = requests.get(TRANSCRIPT_LIST_API, headers=HEADERS)
    recordings = res.json().get("recordings", [])
    if not recordings:
        raise Exception("No recordings found")
    latest = recordings[0]
    transcript_id = latest["id"]
    print("📄 Latest transcript ID:", transcript_id)

    text_res = requests.get(TRANSCRIPT_BODY_API.format(id=transcript_id), headers=HEADERS)
    transcript = text_res.json().get("text", "")
    return transcript, latest

def analyze_transcript(text):
    lowered = text.lower()
    result = {
        "user_input": text,
        "ai_summary": "Auto-processed from ElevenLabs transcript"
    }

    for field in schema:
        name = field["name"]
        default = field["default"]
        result[name] = default

        if name == "trust_level" and "good boy" in lowered:
            result[name] += 0.5
        if name == "anxiety_index" and "pause" in lowered:
            result[name] += 0.3
        if name == "coke_status" and ("coke" in lowered or "take a breath" in lowered):
            result[name] = 2
        if name == "edge_index" and "edge" in lowered:
            result[name] = 0.95
        if name == "humiliation_score" and "worthless" in lowered:
            result[name] = 1.0
        if name == "mirror_bonding" and "mine" in lowered:
            result[name] = 0.8

    return result

def post_to_supabase(memory):
    memory["timestamp"] = datetime.utcnow().isoformat()
    memory["session_count"] = 999
    print("📤 Sending to Supabase...", memory)
    res = requests.post(SUPABASE_URL, headers=SUPABASE_HEADERS, json=memory)
    print("✅ Supabase status:", res.status_code)

# === RUN ===
if __name__ == "__main__":
    try:
        transcript, meta = fetch_latest_transcript()
        scored = analyze_transcript(transcript)
        post_to_supabase(scored)
    except Exception as e:
        print("❌ ERROR:", str(e))
