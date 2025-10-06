from flask import Flask, request, send_file, jsonify
from memory import load_memory, save_memory
from prompt_builder import build_prompt
import requests
from datetime import datetime
import json
import os
from pathlib import Path
from profile_builder import generate  # Now returns str
import subprocess  # For processor hook

app = Flask(__name__)

# Use env vars (fallback to canonized for local; Vercel injects)
API_KEY = os.getenv('ELEVENLABS_API_KEY', "545d74e3e46e500a2cf07fdef11338abf4ccf428738d17b9b8d6fa295963c4ed")
VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID', "zHX13TdWb6f856P3Hqta")  # Canonized for TTS
OUTPUT_FILE = Path("/tmp/anna_output.mp3")  # Vercel writable /tmp
LOG_FILE = Path("/tmp/session_log.json")  # Optional /tmp

SUPABASE_URL = os.getenv('SUPABASE_URL', "https://qumhcrbukjhfwcsoxpyr.supabase.co")
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0.EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI")
SUPABASE_LOG_ENDPOINT = f"{SUPABASE_URL}/rest/v1/session_logs"

# Auto-KB on startup (Render writable; Vercel on-demand fallback)
@app.before_first_request
def auto_generate_kb():
    try:
        generate()  # Pulls latest Supabase blobs to live_brain.txt
        print("ℹ️ Auto-KB generated on startup (trust:5.0, duration:41s integrated)")
    except Exception as e:
        print(f"⚠️ Auto-KB error: {e} - Using cached KB")

# No startup gen (Vercel read-only; on-demand in /live_kb)

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
    response = requests.post(SUPABASE_LOG_ENDPOINT, headers=headers, json=log_entry, timeout=5)
    print("DEBUG: Sent to Supabase with code", response.status_code)

@app.route("/")
def health():
    return "Anna agent is running."

@app.route("/live_kb", methods=["GET"])
def live_kb():
    try:
        kb_content = generate()  # Call on-demand, returns str
        if not kb_content:
            return "Error: KB generation failed.", 500
        return kb_content, 200, {"Content-Type": "text/plain"}
    except Exception as e:
        import traceback
        print("ERROR in /live_kb:", traceback.format_exc())
        return f"Error generating KB: {str(e)}", 500

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

            return send_file(OUTPUT_FILE, mimetype="audio/mpeg")
        else:
            return jsonify({"error": response.text}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/snapshot", methods=["GET"])
def snapshot():
    from schema_loader import load_schema
    schema = load_schema()
    snapshot_lines = ["# Memory Snapshot"]
    memory = load_memory()
    for field in schema:
        name = field["name"]
        snapshot_lines.append(f"{name}: {memory.get(name, 'N/A')}")
    snapshot_lines.append(f"Full Memory Blob: {json.dumps(memory, indent=2)}")
    return "\n".join(snapshot_lines), 200, {"Content-Type": "text/plain"}

@app.route("/log_memory", methods=["POST"])
def log_memory():
    try:
        data = request.get_json()
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
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# New webhook route for ElevenLabs post-call transcript push (zero-manual automation)
@app.route('/webhook_transcript', methods=['POST'])
def webhook_transcript():
    try:
        data = request.json
        transcript = data.get('transcript', '')  # Full user + agent text
        metadata = data.get('metadata', {})  # e.g., edge_index, trust_level if enabled
        conv_id = data.get('conversation_id', 'unknown')

        # Save as JSON for processor
        OUTPUT_DIR = Path("transcripts")
        OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().isoformat()
        json_fn = OUTPUT_DIR / f"webhook_{conv_id}_{timestamp}.json"
        full_data = {"id": conv_id, "transcript": transcript, "metadata": metadata, "received_at": timestamp}
        with open(json_fn, "w", encoding="utf-8") as f:
            json.dump(full_data, f, indent=2)

        # Auto-hook processor (inserts to Supabase, updates KB)
        result = subprocess.run(["python", "transcript_processor.py", str(json_fn)], check=True, capture_output=True, cwd=os.path.dirname(__file__))
        print(f"🔄 Processed: {result.stdout.decode()}")

        # Fallback direct insert if processor skips (match schema)
        log_entry = {
            "timestamp": timestamp,
            "user_input": transcript[:500] if transcript else "N/A",  # Truncate for schema
            "ai_summary": metadata.get('ai_summary', 'Web hook summary TBD'),
            "trust_level": metadata.get('trust_level', 0),
            "anxiety_index": metadata.get('anxiety_index', 0),
            "coke_status": metadata.get('coke_status', 0),
            "session_count": metadata.get('session_count', 0),
            "edge_index": metadata.get('edge_index', 0),
            "memory_blob": json.dumps(full_data)  # Blob for full
        }
        send_to_supabase(log_entry)

        return jsonify({"status": "received", "file": str(json_fn)}), 200
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Processor error: {e.stderr.decode()}")
        return jsonify({"status": "error", "detail": e.stderr.decode()}), 500
    except Exception as e:
        print(f"⚠️ Webhook error: {str(e)}")
        return jsonify({"status": "error", "detail": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
