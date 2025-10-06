import requests
import json
import sys
from datetime import datetime
from schema_loader import load_schema

# === Real API Keys and URLs (Confirmed) ===
ELEVENLABS_API_KEY = "sk_0434e282b02f333781fb7568cb4f9cbbf4449442a1537d36"  # Agents Platform Key
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
    try:
        res = requests.get(TRANSCRIPT_LIST_API, headers=HEADERS)
        if res.status_code != 200:
            raise Exception(f"API fail—use manual (code {res.status_code})")
        recordings = res.json().get("recordings", [])
        if not recordings:
            raise Exception("No recordings found")
        latest = recordings[0]
        transcript_id = latest["id"]
        print("📄 Latest transcript ID:", transcript_id)

        text_res = requests.get(TRANSCRIPT_BODY_API.format(id=transcript_id), headers=HEADERS)
        if text_res.status_code != 200:
            raise Exception(f"API fail—use manual (code {text_res.status_code})")
        transcript = text_res.json().get("text", "")
        return transcript, latest
    except Exception as e:
        print(f"API fail—use manual: {str(e)}")
        # Fallback to mock
        return "Test fallback transcript (API unavailable).", {"id": "fallback"}

def analyze_transcript(text):
    # Coerce to string (handle list/array from API)
    if isinstance(text, list):
        text = ' '.join([item.get('content', str(item)) if isinstance(item, dict) else str(item) for item in text])
    lowered = str(text).lower()
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

    print(f"DEBUG: Blob sample - trust: {memory_blob.get('trust_level', 'MISSING')}, anxiety: {memory_blob.get('anxiety_index', 'MISSING')}")
    return memory_blob

def post_to_supabase(memory_blob, transcript_text, session_duration_secs):
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_count": 999,
        "user_input": transcript_text,
        "ai_summary": "Scored via transcript_processor.py",
        "session_duration_secs": session_duration_secs,  # Mapped from JSON
        "memory_blob": memory_blob
    }
    print(f"DEBUG: Duration mapped: {session_duration_secs}s")
    print("📤 Posting to Supabase:", json.dumps(payload, indent=2))
    res = requests.post(SUPABASE_URL, headers=SUPABASE_HEADERS, json=payload)
    print("✅ Supabase response code:", res.status_code)
    if res.status_code != 201:
        print("❌ Supabase error:", res.text)

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            # Mock mode: Load from JSON file
            with open(sys.argv[1], 'r') as f:
                mock_data = json.load(f)
            transcript = mock_data.get("transcript", "")  # Use "transcript" key from JSON
            session_duration_secs = mock_data.get("duration", 0)  # Pull duration for payload
            print(f"📄 Using mock transcript from {sys.argv[1]}")
        else:
            # Real mode: Fetch from ElevenLabs
            transcript, meta = fetch_latest_transcript()
            session_duration_secs = meta.get("duration", 0) if 'duration' in meta else 0

        memory_blob = analyze_transcript(transcript)
        post_to_supabase(memory_blob, transcript, session_duration_secs)
    except Exception as e:
        print("❌ ERROR:", str(e))
