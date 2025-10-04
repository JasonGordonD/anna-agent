from flask import Flask, request, send_file, jsonify
from memory import load_memory, save_memory
from prompt_builder import build_prompt
import requests
from datetime import datetime
import json
from pathlib import Path
from profile_builder import load_long_term_profile

app = Flask(__name__)

# ElevenLabs config
API_KEY = "545d74e3e46e500a2cf07fdef11338abf4ccf428738d17b9b8d6fa295963c4ed"
VOICE_ID = "qLnOIbrUXZ6axFL6mHX7"
OUTPUT_FILE = Path("anna_output.mp3")
LOG_FILE = Path("session_log.json")

# Supabase config
SUPABASE_URL = "https://qumhcrbukjhfwcsoxpyr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0.EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI"
SUPABASE_LOG_ENDPOINT = f"{SUPABASE_URL}/rest/v1/session_logs"

def analyze_emotion_and_update(memory, user_input):
    lowered = user_input.lower()
    if any(word in lowered for word in ["good boy", "love you", "missed you"]):
        memory["trust_level"] += 0.2
    if any(word in lowered for word in ["i'm scared", "i'm anxious", "i don't know"]):
        memory["anxiety_index"] += 0.1
    if any(word in lowered for word in ["hesitate", "pause", "not sure"]):
        memory["anxiety_index"] += 0.05
        memory["trust_level"] -= 0.05
    if any(word in lowered for word in ["i want to stop", "this is too much", "break"]):
        memory["anxiety_index"] += 0.2
    if "coke" in lowered or "take a breath" in lowered:
        memory["coke_status"] = min(memory.get("coke_status", 0) + 1, 2)

    memory["trust_level"] = round(min(max(memory["trust_level"], 0), 10), 2)
    memory["anxiety_index"] = round(min(max(memory["anxiety_index"], 0), 1), 2)
    return memory

def send_to_supabase(log_entry):
    print("DEBUG: Sending to Supabase:", SUPABASE_LOG_ENDPOINT)
    print("DEBUG: Payload:", json.dumps(log_entry, indent=2))
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(SUPABASE_LOG_ENDPOINT, headers=headers, json=log_entry, timeout=5)
        print("DEBUG: Supabase response code:", response.status_code)
        print("DEBUG: Supabase response body:", response.text)
        if response.status_code != 201:
            print("⚠️ Supabase insert failed:", response.text)
    except Exception as e:
        print("❌ Supabase log error:", e)

@app.route("/")
def health():
    return "Anna agent is running."

@app.route("/speak", methods=["POST"])
def speak():
    try:
        user_input = request.json.get("text")
        if not user_input:
            return jsonify({"error": "Missing 'text' in request."}), 400

        memory = load_memory()
        memory["session_count"] += 1
        memory = analyze_emotion_and_update(memory, user_input)

        prompt = build_prompt(memory)
        text_to_speak = f"{prompt}\n\n{user_input}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": API_KEY
        }
        data = {
            "text": text_to_speak,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.35,
                "similarity_boost": 0.85
            }
        }

        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        response = requests.post(tts_url, headers=headers, json=data)

        if response.status_code == 200:
            with open(OUTPUT_FILE, "wb") as f:
                f.write(response.content)

            save_memory(memory)

            ai_summary = "Neutral compliance."
            if "good boy" in user_input.lower():
                ai_summary = "Reward dynamic reinforced."
            elif "hesitate" in user_input.lower():
                ai_summary = "Emotional resistance detected."

            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_input": user_input,
                "ai_summary": ai_summary,
                "trust_level": memory["trust_level"],
                "anxiety_index": memory["anxiety_index"],
                "coke_status": memory["coke_status"],
                "session_count": memory["session_count"],
                "edge_index": memory.get("edge_index", None)
            }

            with open(LOG_FILE, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

            send_to_supabase(log_entry)

            return send_file(OUTPUT_FILE, mimetype="audio/mpeg")
        else:
            return jsonify({"error": response.text}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/snapshot", methods=["GET"])
def snapshot():
    memory = load_memory()
    try:
        composite_profile = load_long_term_profile()
    except Exception:
        composite_profile = "No long-term profile available."

    snapshot_text = f"""# Memory Snapshot
trust_level: {memory.get('trust_level', 'N/A')}
session_count: {memory.get('session_count', 'N/A')}
anxiety_index: {memory.get('anxiety_index', 'N/A')}
coke_status: {memory.get('coke_status', 'N/A')}
edge_index: {memory.get('edge_index', 'N/A')}

# Composite Profile
{composite_profile}
"""
    return snapshot_text, 200, {"Content-Type": "text/plain"}

@app.route("/log_memory", methods=["POST"])
def log_memory():
    try:
        data = request.get_json()
        print("DEBUG: Incoming /log_memory call")
        print("DEBUG: Received data:", data)

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_input": data.get("user_input", ""),
            "trust_level": data.get("trust_level"),
            "anxiety_index": data.get("anxiety_index"),
            "coke_status": data.get("coke_status"),
            "session_count": data.get("session_count"),
            "edge_index": data.get("edge_index"),
            "ai_summary": data.get("ai_summary", "N/A")
        }

        send_to_supabase(log_entry)

        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
