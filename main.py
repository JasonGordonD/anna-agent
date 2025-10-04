import json
from flask import Flask, request, send_file, jsonify
from memory import load_memory, save_memory
from prompt_builder import build_prompt
from datetime import datetime
from pathlib import Path
from profile_builder import load_long_term_profile
import requests

app = Flask(__name__)

API_KEY = "545d74e3e46e500a2cf07fdef11338abf4ccf428738d17b9b8d6fa295963c4ed"
VOICE_ID = "qLnOIbrUXZ6axFL6mHX7"
OUTPUT_FILE = Path("anna_output.mp3")
LOG_FILE = Path("session_log.json")
SUPABASE_URL = "https://qumhcrbukjhfwcsoxpyr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0.EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI"
SUPABASE_LOG_ENDPOINT = f"{SUPABASE_URL}/rest/v1/session_logs"

with open("memory_schema.json") as f:
    MEMORY_SCHEMA = json.load(f)

def send_to_supabase(log_entry):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(SUPABASE_LOG_ENDPOINT, headers=headers, json=log_entry, timeout=5)
    print("DEBUG: Supabase response code:", response.status_code)

@app.route("/log_memory", methods=["POST"])
def log_memory():
    try:
        data = request.get_json()
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_input": data.get("user_input", ""),
            "ai_summary": data.get("ai_summary", "N/A")
        }
        for field in MEMORY_SCHEMA:
            name = field["name"]
            default = field["default"]
            log_entry[name] = data.get(name, default)
        send_to_supabase(log_entry)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/snapshot", methods=["GET"])
def snapshot():
    memory = load_memory()
    try:
        composite_profile = load_long_term_profile()
    except Exception:
        composite_profile = "No long-term profile available."

    snapshot_lines = ["# Memory Snapshot"]
    for field in MEMORY_SCHEMA:
        name = field["name"]
        snapshot_lines.append(f"{name}: {memory.get(name, 'N/A')}")
    snapshot_lines.append("
# Composite Profile
" + composite_profile)

    return "
".join(snapshot_lines), 200, {"Content-Type": "text/plain"}

@app.route("/live_kb", methods=["GET"])
def live_kb():
    try:
        with open("live_brain.txt", "r") as f:
            return f.read(), 200, {"Content-Type": "text/plain"}
    except FileNotFoundError:
        return "No live KB available.", 200, {"Content-Type": "text/plain"}

@app.route("/speak", methods=["POST"])
def speak():
    try:
        user_input = request.json.get("text")
        if not user_input:
            return jsonify({"error": "Missing 'text' in request."}), 400

        memory = load_memory()
        memory["session_count"] += 1
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
                "edge_index": memory["edge_index"],
                "session_count": memory["session_count"]
            }

            with open(LOG_FILE, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

            send_to_supabase(log_entry)

            return send_file(OUTPUT_FILE, mimetype="audio/mpeg")
        else:
            return jsonify({"error": response.text}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def health():
    return "Anna agent is running."