from flask import Flask, request, send_file, jsonify
from memory import load_memory, save_memory
from prompt_builder import build_prompt
import requests
from datetime import datetime
import json
import os
from pathlib import Path
from profile_builder import generate
import subprocess
import hmac
import hashlib
import time

app = Flask(__name__)

# === CONFIGURATION ===
API_KEY = os.getenv('ELEVENLABS_API_KEY', "545d74e3e46e500a2cf07fdef11338abf4ccf428738d17b9b8d6fa295963c4ed")
VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID', "zHX13TdWb6f856P3Hqta")
OUTPUT_FILE = Path("/tmp/anna_output.mp3")
LOG_FILE = Path("/tmp/session_log.json")
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', "")
SUPABASE_URL = os.getenv('SUPABASE_URL', "https://qumhcrbukjhfwcsoxpyr.supabase.co")
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0.EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI")
SUPABASE_LOG_ENDPOINT = f"{SUPABASE_URL}/rest/v1/session_logs"

# === KB GENERATION ON STARTUP ===
try:
    generate()
    print("ℹ️ Auto-KB generated on startup (trust:5.0, duration:41s integrated)")
except Exception as e:
    print(f"⚠️ Auto-KB error: {e} - Using cached KB")


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
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    response = requests.post(
        SUPABASE_LOG_ENDPOINT + "?on_conflict=conversation_id",
        headers=headers,
        json=log_entry,
        timeout=5,
    )
    print("DEBUG: Supabase upsert code:", response.status_code)
    return response


@app.route("/")
def health():
    return "Anna agent is running."


@app.route("/live_kb", methods=["GET"])
def live_kb():
    try:
        kb_content = generate()
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
        memory = analyze_emotion_and_update(memory, user_input)
        save_memory(memory)
        prompt = build_prompt(user_input, memory)
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": API_KEY,
        }
        data = {
            "text": prompt,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
            json=data,
            headers=headers,
        )
        if response.status_code == 200:
            OUTPUT_FILE.parent.mkdir(exist_ok=True)
            with open(OUTPUT_FILE, "wb") as f:
                f.write(response.content)
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_input": user_input,
                "trust_level": memory["trust_level"],
                "anxiety_index": memory["anxiety_index"],
                "coke_status": memory["coke_status"],
                "session_count": memory["session_count"],
                "edge_index": memory["edge_index"],
                "ai_summary": "Generated via /speak endpoint",
            }
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
            "ai_summary": data.get("ai_summary", "N/A"),
        }
        send_to_supabase(log_entry)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === Updated webhook_transcript (Option A) ===
@app.route("/webhook_transcript", methods=["POST"])
def webhook_transcript():
    try:
        signature_header = request.headers.get("ElevenLabs-Signature", "")
        if not signature_header:
            return jsonify({"error": "Missing signature"}), 401
        parts = signature_header.split(",")
        timestamp_part = parts[0].strip()[2:] if parts else ""
        signature_part = parts[1].strip() if len(parts) > 1 else ""
        raw_body = request.get_data(as_text=True)
        tolerance = int(time.time()) - 30 * 60
        if int(timestamp_part or 0) < tolerance:
            return jsonify({"error": "Stale timestamp"}), 403
        full_payload = f"{timestamp_part}.{raw_body}"
        computed_hmac = hmac.new(
            WEBHOOK_SECRET.encode("utf-8"),
            full_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        expected_sig = f"v0={computed_hmac}"
        if signature_part != expected_sig:
            return jsonify({"error": "Invalid signature"}), 403

        data = request.json
        if not data or data.get("type") != "post_call_transcription":
            return jsonify({"error": "Invalid payload type"}), 400

        payload = data["data"]
        conv_id = payload["conversation_id"]
        agent_id = payload["agent_id"]
        if payload.get("status", "unknown") != "done":
            return jsonify({"status": "queued", "id": conv_id}), 202

        transcript = payload.get("transcript", [])
        metadata = payload.get("metadata", {})
        cost = metadata.get("cost", 0.0)
        feedback = metadata.get("feedback", {}) or {}

        from transcript_processor import process_transcript
        result = process_transcript(agent_id, conv_id, transcript, metadata, cost, feedback)

        OUTPUT_DIR = Path("transcripts")
        OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().isoformat()
        json_fn = OUTPUT_DIR / f"webhook_{conv_id}_{timestamp}.json"
        with open(json_fn, "w", encoding="utf-8") as f:
            json.dump({"id": conv_id, "data": result, "received_at": timestamp}, f, indent=2)

        subprocess.run(
            ["python", "git_sync.py"],
            check=True,
            capture_output=True,
            cwd=os.path.dirname(__file__),
        )

        return jsonify(result), 200

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Processor error: {e.stderr.decode()}")
        return jsonify({"status": "error", "detail": e.stderr.decode()}), 500
    except Exception as e:
        import traceback
        print(f"⚠️ Webhook error: {traceback.format_exc()}")
        return jsonify({"status": "error", "detail": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
