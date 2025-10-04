from memory import load_memory, save_memory
from prompt_builder import build_prompt
import requests

memory = load_memory()
prompt = build_prompt(memory)

# Call ElevenLabs API
response = requests.post(
    "https://api.elevenlabs.io/v1/your-agent-endpoint",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={"prompt": prompt, "text": "Hey, Anna."}
)

# Update memory as needed
memory["session_count"] += 1
save_memory(memory)

print(response.json())
