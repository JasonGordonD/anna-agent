from flask import Flask, request, send_file, jsonify
from memory import load_memory, save_memory
from prompt_builder import build_prompt
import requests
from datetime import datetime
import json
from pathlib import Path
from schema_loader import load_schema

app = Flask(__name__)

API_KEY = "545d74e3e46e500a2cf07fdef11338abf4ccf428738d17b9b8d6fa295963c4ed"
VOICE_ID = "qLnOIbrUXZ6axFL6mHX7"
OUTPUT_FILE = Path("anna_output.mp3")
LOG_FILE = Path("session_log.json")

SUPABASE_URL = "https://qumhcrbukjhfwcsoxpyr.supabase.co/rest/v1/session_logs"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0.EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI"
SUPABASE_LOG_ENDPOINT = SUPABASE_URL

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
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(SUPABASE_LOG_ENDPOINT, headers=headers, json=log_entry, timeout=5)
        print("DEBUG: Supabase response code:", response.status_code)
        if response.status_code != 201:
            print("⚠️ Supabase insert failed:", response.text)
    except Exception as e:
        print("❌ Supabase log error:", e)

@app.route("/", methods=["GET"])
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

        # Instead of generating audio, return the transcript (text_to_speak) as JSON
        # This focuses on transcripts, not audio files
        save_memory(memory)

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_input": user_input,
            "ai_summary": "Auto summary TBD",
            "trust_level": memory["trust_level"],
            "anxiety_index": memory["anxiety_index"],
            "coke_status": memory["coke_status"],
            "session_count": memory["session_count"],
            "edge_index": memory.get("edge_index")
        }

        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        send_to_supabase(log_entry)

        return jsonify({"transcript": text_to_speak}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/live_kb", methods=["GET"])
def live_kb():
    try:
        with open("live_brain.txt", "r") as f:
            return f.read(), 200, {"Content-Type": "text/plain"}
    except Exception as e:
        return f"Error loading KB: {str(e)}", 500

@app.route("/snapshot", methods=["GET"])
def snapshot():
    memory = load_memory()
    schema = load_schema()
    snapshot_lines = ["# Memory Snapshot"]
    for field in schema:
        name = field["name"]
        snapshot_lines.append(f"{name}: {memory.get(name, 'N/A')}")
    return "\n".join(snapshot_lines), 200, {"Content-Type": "text/plain"}

@app.route("/log_memory", methods=["POST"])
def log_memory():
    print("DEBUG /log_memory called, headers:", request.headers)
    print("DEBUG body:", request.get_data())
    try:
        data = request.get_json()
        schema = load_schema()
        log_entry = {
            "timestamp": datetime.utcnow().isoformat()
        }
        for field in schema:
            name = field["name"]
            log_entry[name] = data.get(name, field["default"])
        log_entry["user_input"] = data.get("user_input", "")
        log_entry["ai_summary"] = data.get("ai_summary", "N/A")
        log_entry["session_count"] = data.get("session_count", 999)
        send_to_supabase(log_entry)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
