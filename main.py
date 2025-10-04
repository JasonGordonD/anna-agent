from flask import Flask, request, send_file, jsonify
from memory import load_memory, save_memory
from prompt_builder import build_prompt
import requests
from pathlib import Path

# ✅ This line must be top-level for gunicorn to find it
app = Flask(__name__)

# ElevenLabs config
API_KEY = "545d74e3e46e500a2cf07fdef11338abf4ccf428738d17b9b8d6fa295963c4ed"
VOICE_ID = "qLnOIbrUXZ6axFL6mHX7"
OUTPUT_FILE = Path("anna_output.mp3")

@app.route("/")
def health():
    return "Anna agent is running."

@app.route("/speak", methods=["POST"])
def speak():
    try:
        user_input = request.json.get("text")
        if not user_input:
            return jsonify({"error": "Missing 'text' in request."}), 400

        # Load memory and build prompt
        memory = load_memory()
        prompt = build_prompt(memory)
        text_to_speak = f"{prompt}\n\n{user_input}"

        # Send request to ElevenLabs TTS
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

        # Handle response
        if response.status_code == 200:
            with open(OUTPUT_FILE, "wb") as f:
                f.write(response.content)

            memory["session_count"] += 1
            memory["trust_level"] += 0.1
            save_memory(memory)

            return send_file(OUTPUT_FILE, mimetype="audio/mpeg")
        else:
            return jsonify({"error": response.text}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
