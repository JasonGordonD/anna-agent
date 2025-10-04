import requests
import json
from datetime import datetime
from schema_loader import load_schema

# === Real API Keys and URLs (Confirmed) ===
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
    memory_blob = {}

    for field in schema:
        name = field["name"]
        default = field["default"]
        memory_blob[name] = default

        if name == "trust_level" and "good boy" in lowered:
            memory_blob[name] += 0.5
        if name == "anxiety_index" and "pause" in lowered:
            memory_blob[name] += 0.3
        if name == "coke_status" and ("coke" in lowered or "take a breath" in lowered):
            memory_blob[name] = 2
        if name == "edge_index" and "edge" in lowered:
            memory_blob[name] = 0.95
        if name == "humiliation_score" and "worthless" in lowered:
            memory_blob[name] = 1.0
        if name == "mirror_bonding" and "mine" in lowered:
            memory_blob[name] = 0.8

    return memory_blob

def post_to_supabase(memory_blob, transcript_text):
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_count": 999,
        "user_input": transcript_text,
        "ai_summary": "Scored via transcript_processor.py",
        "memory_blob": memory_blob
    }
    print("📤 Posting to Supabase:", json.dumps(payload, indent=2))
    res = requests.post(SUPABASE_URL, headers=SUPABASE_HEADERS, json=payload)
    print("✅ Supabase response code:", res.status_code)
    if res.status_code != 201:
        print("❌ Supabase error:", res.text)

if __name__ == "__main__":
    try:
        transcript, meta = fetch_latest_transcript()
        memory_blob = analyze_transcript(transcript)
        post_to_supabase(memory_blob, transcript)
    except Exception as e:
        print("❌ ERROR:", str(e))