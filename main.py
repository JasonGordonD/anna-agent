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
API_KEY = "sk_395144d7d8604f470abb8d983081770c371c3011e03962e7"
VOICE_ID = "zHX13TdWb6f856P3Hqta"
OUTPUT_FILE = Path("/tmp/anna_output.mp3")
LOG_FILE = Path("/tmp/session_log.json")
WEBHOOK_SECRET = "wsec_5d8d7f341e697527d4e60a51c30d04e208aa88f30c6ec5a77a158e97ce13be19"
SUPABASE_URL = "https://qumhcrbukjhfwcsoxpyr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0.EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI"
SUPABASE_LOG_ENDPOINT = f"{SUPABASE_URL}/rest/v1/session_logs"
CARTESIA_API_KEY = os.getenv('CARTESIA_API_KEY', "sk_car_wkFkGShryW7kszY8uT6r7L")

# === USER ID EXTRACTION ===
def get_user_id():
    """Extract user_id from request: header > query param > payload > default 'billy'."""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        user_id = request.args.get('user_id')
    # Fixed: Guard JSON parse—only on POST, with try/except to avoid 415/500 on GET
    if not user_id and request.method == 'POST':
        try:
            user_id = request.json.get('user_id') if request.json else None
        except:
            pass  # Skip parse on non-JSON or unsupported type
    return user_id or 'billy'

# === BUILD DYNAMIC ELEVENLABS VARIABLES ===
def build_dynamic_vars(user_id, memory):
    """Build ElevenLabs dynamic variable payload per user."""
    persona_role = "sub" if user_id == "billy" else ("admin" if user_id == "rami" else "self")
    visible_user_id = "anna" if user_id == "anna_self" else user_id
    kb_context = {
        "content": f"KB:Anna-v1.1 Persona:{visible_user_id} Role:{persona_role}"
    }
    return {
        "toolfetch_memory": json.dumps(memory),
        "toolfetch_kb_anna": json.dumps(kb_context),
        "user_id": visible_user_id
    }

# === KB GENERATION ON STARTUP ===
try:
    generate()
    print("ℹ️ Auto-KB generated on startup (trust:5.0, duration:41s integrated)")
except Exception as e:
    print(f"⚠️ Auto-KB error: {e} - Using cached KB")

# === EMOTION ANALYSIS ===
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

# === SUPABASE LOG ===
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
    )
    if response.status_code != 201:
        print(f"[supabase] Log failed {response.status_code}: {response.text}")

@app.route("/", methods=["GET", "HEAD"])
def health_check():
    return "Anna agent is running.", 200, {"Content-Type": "text/plain"}

@app.route("/live_kb", methods=["GET"])
def live_kb():
    try:
        user_id = get_user_id()
        kb_text = generate(user_id)
        return jsonify({"kb": kb_text}), 200
    except Exception as e:
        print(f"ERROR in /live_kb: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/snapshot", methods=["GET"])
def snapshot():
    try:
        user_id = get_user_id()
        memory = load_memory(user_id)
        return jsonify(memory), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/speak", methods=["POST"])
def speak():
    try:
        data = request.get_json()
        text = data.get("text", "")
        user_id = get_user_id()
        memory = load_memory(user_id)
        memory = analyze_emotion_and_update(memory, text)
        save_memory(user_id, memory)
        dynamic_vars = build_dynamic_vars(user_id, memory)
        prompt = build_prompt(text, memory, dynamic_vars)
        headers = {
            "Authorization": f"Bearer {CARTESIA_API_KEY}",
            "Content-Type": "application/json",
            "Cartesia-Version": "2025-04-16"
        }
        tts_payload = {
            "text": prompt,
            "voice": "sonic-ro-female",
            "model": "sonic-2",
            "speed": 1.0,
            "format": "mp3"
        }
        response = requests.post("https://api.cartesia.ai/v1/tts/bytes", headers=headers, json=tts_payload)
        if response.status_code == 200:
            OUTPUT_FILE.write_bytes(response.content)
            return send_file(OUTPUT_FILE, mimetype="audio/mpeg")
        return jsonify({"error": "TTS failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/log_memory", methods=["POST"])
def log_memory():
    try:
        user_id = get_user_id()
        data = request.get_json()
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
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

# === WEBHOOK HANDLER ===
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

        user_id = get_user_id()
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

        OUTPUT_DIR = Path(f"transcripts/{user_id}")
        OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
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
