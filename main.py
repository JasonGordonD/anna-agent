from flask import Flask, request, send_file, jsonify
from memory import load_memory, save_memory
from prompt_builder import build_prompt
import requests
from pathlib import Path
from datetime import datetime
import json

app = Flask(__name__)

# ElevenLabs configuration
API_KEY = "545d74e3e46e500a2cf07fdef11338abf4ccf428738d17b9b8d6fa295963c4ed"
VOICE_ID = "qLnOIbrUXZ6axFL6mHX7"
OUTPUT_FILE = Path("anna_output.mp3")
LOG_FILE = Path("session_log.json")


def generate_memory_snapshot(memory):
    return f"""# Memory Snapshot
trust_level: {memory['trust_level']}
session_count: {memory['session_count']}
anxiety_index: {memory['anxiety_index']}
coke_status: {memory['coke_status']}

Resume interaction with Billy as if it's a continuous, emotionally layered scene.
"""


def analyze_emotion_and_update(memory, user_input):
    """Basic emotional parser to adjust memory heuristically."""
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
        memory["coke_status"] = min(memory["coke_status"] + 1, 2)

    # Clamp values within valid range
    memory["trust_level"] = round(min(max(memory["trust_level"], 0), 10), 2)
    memory["anxiety_index"] = round(min(max(memory["anxiety_index"], 0), 1), 2)

    return memory


def generate_ai_summary(user_input, memory):
    """Simulated AI-style summary log of user interaction."""
    if "good boy" in user_input.lower():
        tone = "Reward dynamic reinforced."
    elif "hesitate" in user_input.lower():
        tone = "Emotional resistance detected."
    elif "missed" in user_input.lower():
        tone = "Emotional longing expressed."
    else:
        tone = "Neutral compliance."

    return f"{tone} Trust: {memory['trust_level']} | Anxiety: {memory['anxiety_index']} | Coke Status: {memory['coke_status']}"


@app.route("/")
def health():
    return "Anna agent is running."


@app.route("/speak", methods=["POST"])
def speak():
    try:
        user_input = request.json.get("text")
        if not user_input:
            return jsonify({"error": "Missing 'text' in request."}), 400

        # Load memory, analyze, and update
        memory = load_memory()
        memory["session_count"] += 1
        memory = analyze_emotion_and_update(memory, user_input)

        # Build prompt and full text
        prompt = build_prompt(memory)
        text_to_speak = f"{prompt}\n\n{user_input}"

        # ElevenLabs request
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
            # Save audio
            with open(OUTPUT_FILE, "wb") as f:
                f.write(response.content)

            # Save updated memory
            save_memory(memory)

            # Log session
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_input": user_input,
                "memory_snapshot": memory,
                "ai_summary": generate_ai_summary(user_input, memory)
            }
            with open(LOG_FILE, "a") as log_file:
                log_file.write(json.dumps(log_entry) + "\n")

            return send_file(OUTPUT_FILE, mimetype="audio/mpeg")

        else:
            return jsonify({"error": response.text}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/snapshot", methods=["GET"])
def snapshot():
    memory = load_memory()
    return generate_memory_snapshot(memory), 200, {"Content-Type": "text/plain"}
