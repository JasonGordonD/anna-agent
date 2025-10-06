# get_transcripts.py — download and save transcripts for each conversation
import os, requests, json
from pathlib import Path
from datetime import datetime

# === CONFIGURATION ===
API_KEY = os.getenv("XI_API_KEY") or "1232ea6af7f2a81ecba73b2a8d551c189bfd131e5d533f70a42373091383b756"
AGENT_ID = "agent_2901k6qjvk71e9cbftde9wzyt94n"
HEADERS = {"xi-api-key": API_KEY}
OUT = Path("transcripts")
OUT.mkdir(exist_ok=True)

print("🎧 Downloading full transcripts for each conversation...")

# --- get list of conversations ---
list_url = "https://api.elevenlabs.io/v1/convai/conversations"
r = requests.get(list_url, headers=HEADERS, timeout=15)
if r.status_code != 200:
    raise SystemExit(f"❌ Could not list conversations: {r.status_code} - {r.text}")
convs = r.json().get("conversations", [])
print(f"📄 Found {len(convs)} conversations.")

for c in convs:
    cid = c["conversation_id"]
    title = c.get("call_summary_title", "Untitled")
    turl = f"https://api.elevenlabs.io/v1/agents/{AGENT_ID}/conversations/{cid}/transcript"
    resp = requests.get(turl, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        print(f"⚠️ Skipping {cid} ({resp.status_code})")
        continue
    data = resp.json()
    fn = OUT / f"{cid}_{datetime.utcnow().isoformat()}.json"
    with open(fn, "w", encoding="utf-8") as f:
        json.dump({"conversation": c, "transcript": data}, f, indent=2)
    print(f"✅ Saved transcript: {title} → {fn}")
