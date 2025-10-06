# list_conversations.py — fetch & save all ElevenLabs conversations
import requests
import json
import os
from datetime import datetime

# === CONFIGURATION ===
API_KEY = os.getenv("XI_API_KEY") or "1232ea6af7f2a81ecba73b2a8d551c189bfd131e5d533f70a42373091383b756"
BASE_URL = "https://api.elevenlabs.io/v1/convai/conversations"
HEADERS = {"xi-api-key": API_KEY}
ALL = []
cursor = None

print("🎧 Fetching conversations from ElevenLabs ConvAI API...")

while True:
    params = {"cursor": cursor} if cursor else {}
    r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)
    if r.status_code == 401:
        raise SystemExit("❌ Unauthorized. Check your API key or environment variable XI_API_KEY.")
    if r.status_code != 200:
        raise SystemExit(f"❌ API error {r.status_code}: {r.text}")

    data = r.json()
    convs = data.get("conversations", [])
    print(f"📄 Retrieved {len(convs)} conversations (batch).")
    ALL.extend(convs)
    if not data.get("has_more"):
        break
    cursor = data.get("next_cursor")

out_file = f"conversations_{datetime.now().isoformat()}.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(ALL, f, indent=2)
print(f"✅ Saved {len(ALL)} conversations to {out_file}")
