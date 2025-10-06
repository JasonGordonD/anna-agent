import requests
import json
import subprocess
import os

# Canonized creds (treat as test—change post-launch)
SUPABASE_URL = "https://qumhcrbukjhfwcsoxpyr.supabase.co/rest/v1/session_logs"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0.EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI"
RENDER_URL = "https://anna-agent.onrender.com"
ELEVENLABS_KEY = "sk_395144d7d8604f470abb8d983081770c371c3011e03962e7"
VOICE_ID = "zHX13TdWb6f856P3Hqta"

headers_supabase = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}
headers_elevenlabs = {"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"}

def check_render_wake():
    resp = requests.get(f"{RENDER_URL}/")
    return resp.status_code == 200 and "Anna agent is running" in resp.text

def test_speak_tts(text="Test session start."):
    payload = {"text": text, "voice_id": VOICE_ID, "model_id": "eleven_monolingual_v1"}
    resp = requests.post("https://api.elevenlabs.io/v1/text-to-speech/eleven_monolingual_v1", json=payload, headers=headers_elevenlabs)
    return resp.status_code == 200 and resp.headers.get("content-type", "").startswith("audio/")

def test_log_memory():
    # Pre-count rows
    count_resp = requests.get(SUPABASE_URL, headers=headers_supabase)
    pre_count = len(count_resp.json()) if count_resp.status_code == 200 else 0

    # Mock payload (from schema: blob, duration_secs, etc.)
    mock_blob = json.dumps({"trust": 4.5, "anxiety": 2.1, "turns": [{"role": "user", "message": "Test log."}]})
    payload = {
        "memory_blob": mock_blob,
        "session_duration_secs": 45,
        "trust_level": 4.5,
        "anxiety_index": 2.1
    }
    insert_resp = requests.post(SUPABASE_URL, json=[payload], headers=headers_supabase)
    
    # Post-count
    count_resp = requests.get(SUPABASE_URL, headers=headers_supabase)
    post_count = len(count_resp.json()) if count_resp.status_code == 200 else 0
    
    return insert_resp.status_code == 201 and post_count == pre_count + 1

def test_process_and_kb():
    # Assume log_memory inserted row N; now process via profile_builder (local run)
    os.system("python profile_builder.py")  # Generates live_brain.txt from Supabase
    kb_resp = requests.get(f"{RENDER_URL}/live_kb")
    return kb_resp.status_code == 200 and "trust" in kb_resp.text.lower()  # KB updated with new data

def test_graph():
    os.system("python emotion_grapher.py")  # Generates PDF from logs
    return os.path.exists("emotion_graph.pdf")  # File created

# Run E2E
print("=== Phase 4 E2E Check ===")
tests = [
    ("Render Wake", check_render_wake()),
    ("TTS /speak", test_speak_tts()),
    ("Supabase /log_memory", test_log_memory()),
    ("Process → KB Update", test_process_and_kb()),
    ("Emotion Graph", test_graph())
]
passed = sum(1 for _, p in tests if p)
for name, result in tests:
    print(f"{name}: {'✅' if result else '❌'}")
print(f"Overall: {passed}/5 passed. Delta expected: +1 Supabase row, updated KB, PDF generated.")
