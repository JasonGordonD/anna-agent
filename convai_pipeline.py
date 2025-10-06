import json
import subprocess
from pathlib import Path
from list_conversations import fetch_conversations  # Assumes your existing func
from get_transcripts import fetch_transcript  # Existing
from transcript_processor import process_transcript
import requests  # For Supabase direct if needed

SUPABASE_ENDPOINT = "https://qumhcrbukjhfwcsoxpyr.supabase.co/rest/v1/session_logs"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0.EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI"
AGENT_ID = "agent_2901k6qjvk71e9cbftde9wzyt94n"
API_KEY = "sk_395144d7d8604f470abb8d983081770c371c3011e03962e7"

def sync_pipeline(limit=5):  # Dry run top N
    convos = fetch_conversations(limit=limit)  # Returns list of {"id": conv_id, "metadata": {...}}
    for convo in convos:
        conv_id = convo["id"]
        metadata = convo["metadata"]
        transcript = fetch_transcript(AGENT_ID, conv_id)  # 200/turns if toggle ON
        if transcript:
            result = process_transcript(AGENT_ID, conv_id, transcript, metadata, cost=0.0, feedback={})
            # Supabase upsert
            headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"}
            log_entry = {"conversation_id": conv_id, "timestamp": metadata.get("timestamp"), "user_input": json.dumps(transcript), "ai_summary": "Auto-synced historical", "memory_blob": result["analysis"], "session_duration_secs": metadata.get("duration", 0)}
            requests.post(f"{SUPABASE_ENDPOINT}?on_conflict=conversation_id", headers=headers, json=log_entry)
            # Git archive
            OUTPUT_DIR = Path("transcripts")
            OUTPUT_DIR.mkdir(exist_ok=True)
            with open(OUTPUT_DIR / f"historical_{conv_id}.json", "w") as f:
                json.dump({"id": conv_id, "transcript": transcript, "analysis": result}, f, indent=2)
    subprocess.run(["python", "git_sync.py"], check=True)
    print(f"Synced {len(convos)} convos; check Supabase rows 39+ and GitHub transcripts/")

if __name__ == "__main__":
    sync_pipeline(limit=5)  # Scale to 442 after dry
