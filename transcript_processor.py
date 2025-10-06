import requests
import json
import sys
from datetime import datetime
from schema_loader import load_schema

ELEVENLABS_API_KEY = "sk_0434e282b02f333781fb7568cb4f9cbbf4449442a1537d36"
SUPABASE_URL = "https://qumhcrbukjhfwcsoxpyr.supabase.co/rest/v1/session_logs"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0."
    "EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI"
)

# Updated to ConvAI endpoints per canon (recordings → convai/conversations)
TRANSCRIPT_LIST_API = "https://api.elevenlabs.io/v1/convai/conversations"
TRANSCRIPT_BODY_API = "https://api.elevenlabs.io/v1/convai/conversations/{id}"

HEADERS = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

schema = load_schema()


def fetch_latest_transcript():
    print("Fetching transcript IDs ...")
    try:
        res = requests.get(TRANSCRIPT_LIST_API, headers=HEADERS)
        if res.status_code != 200:
            raise Exception(f"API fail (code {res.status_code})")
        conversations = res.json().get("conversations", [])
        if not conversations:
            raise Exception("No conversations found")
        latest = conversations[0]
        conv_id = latest["id"]
        print("Latest conversation ID:", conv_id)
        text_res = requests.get(
            TRANSCRIPT_BODY_API.format(id=conv_id), headers=HEADERS
        )
        if text_res.status_code != 200:
            raise Exception(f"API fail (code {text_res.status_code})")
        transcript = text_res.json().get("transcript", [])
        return transcript, latest
    except Exception as e:
        print("API fail:", str(e))
        return "Test fallback transcript (API unavailable).", {"id": "fallback"}


def analyze_transcript(text):
    """Analyze transcript text against schema to build memory_blob."""
    if isinstance(text, list):
        text = " ".join(
            [item.get("content", str(item)) if isinstance(item, dict) else str(item) for item in text]
        )
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
    print("DEBUG blob:", memory_blob)
    return memory_blob


def post_to_supabase(memory_blob, transcript_text, session_duration_secs):
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_count": 999,
        "user_input": transcript_text,
        "ai_summary": "Scored via transcript_processor.py",
        "session_duration_secs": session_duration_secs,
        "memory_blob": memory_blob,
    }
    print("Posting to Supabase ...")
    res = requests.post(SUPABASE_URL, headers=SUPABASE_HEADERS, json=payload)
    print("Supabase response code:", res.status_code)
    if res.status_code != 201:
        print("Supabase error:", res.text)


def process_transcript(agent_id, conversation_id, transcript, metadata, cost, feedback):
    """Called from webhook_transcript in main.py."""
    print(f"Processing transcript for agent={agent_id}, conversation={conversation_id}")
    if isinstance(transcript, list):
        # Fixed: Coerce None to '' to avoid TypeError in join
        transcript_text = "\n".join(
            [m.get("message", str(m)) if isinstance(m, dict) else (str(m) if m is not None else '') for m in transcript]
        )
    else:
        transcript_text = str(transcript)
    duration = 0
    if isinstance(metadata, dict):
        duration = metadata.get("call_duration_secs", 0)
    memory_blob = analyze_transcript(transcript_text)
    post_to_supabase(memory_blob, transcript_text, duration)
    return {
        "status": "processed",
        "agent_id": agent_id,
        "conversation_id": conversation_id,
        "feedback": feedback,
        "cost": cost,
        "analysis": memory_blob,
    }


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            with open(sys.argv[1], "r") as f:
                mock_data = json.load(f)
            transcript = mock_data.get("transcript", "")
            session_duration_secs = mock_data.get("duration", 0)
            print(f"Using mock transcript from {sys.argv[1]}")
        else:
            transcript, meta = fetch_latest_transcript()
            session_duration_secs = meta.get("duration", 0) if "duration" in meta else 0
        memory_blob = analyze_transcript(transcript)
        post_to_supabase(memory_blob, transcript, session_duration_secs)
    except Exception as e:
        print("ERROR:", str(e))
