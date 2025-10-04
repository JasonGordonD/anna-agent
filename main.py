from memory import load_memory, save_memory
from prompt_builder import build_prompt
import requests
from pathlib import Path

# 1. Load current session memory
memory = load_memory()

# 2. Build the dynamic system prompt
prompt = build_prompt(memory)

# 3. The text Anna will speak
anna_text = "Hey Billy... bakery on 7th still? Terrible espresso, nu?"

# 4. Combine memory-driven prompt + speaking text
text_to_speak = f"{prompt}\n\n{anna_text}"

# 5. ElevenLabs API configuration
API_KEY = "545d74e3e46e500a2cf07fdef11338abf4ccf428738d17b9b8d6fa295963c4ed"
VOICE_ID = "qLnOIbrUXZ6axFL6mHX7"  # Your Anna voice
OUTPUT_FILE = Path("anna_output.mp3")

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
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

print("Sending request to ElevenLabs...")
response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    with open(OUTPUT_FILE, "wb") as f:
        f.write(response.content)
    print(f"✅ Audio saved to {OUTPUT_FILE}")
else:
    print("❌ Error:", response.status_code, response.text)

# 6. Update memory after session
memory["session_count"] += 1
memory["trust_level"] += 0.1
save_memory(memory)
print("🧠 Memory updated:", memory)
