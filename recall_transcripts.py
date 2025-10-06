import requests
import json
import os
from datetime import datetime
import time

API_KEY = os.getenv("XI_API_KEY", "sk_0434e282b02f333781fb7568cb4f9cbbf4449442a1537d36")  # Agents key default
AGENT_ID = "agent_2901k6qjvk71e9cbftde9wzyt94n"
BASE_URL = "https://api.elevenlabs.io/v1"
HEADERS = {"xi-api-key": API_KEY}

transcripts_dir = "transcripts"
os.makedirs(transcripts_dir, exist_ok=True)

print(f"ℹ️ Using key: {API_KEY[:10]}...{API_KEY[-4:]} | Agent: {AGENT_ID}")

# Step 1: List conversations (paginated, max 100) with debug & retry
conversations = []
cursor = None
page = 1
max_retries = 3
while True:
    params = {"agent_id": AGENT_ID, "limit": 100}
    if cursor:
        params["next_cursor"] = cursor
    print(f"ℹ️ Page {page}: Params {params}")
    for retry in range(max_retries):
        response = requests.get(f"{BASE_URL}/convai/conversations", headers=HEADERS, params=params)
        print(f"ℹ️ Status: {response.status_code} | Response preview: {response.text[:200]}...")
        if response.status_code == 200:
            break
        elif response.status_code in [401, 404]:
            print(f"⚠️ {response.status_code}: Key/Agent issue—check export/UI link")
            exit(1)
        else:
            print(f"⚠️ Retry {retry+1}/{max_retries}: {response.status_code} - {response.text[:100]}")
            time.sleep(2 ** retry)  # Expo backoff
    else:
        print("⚠️ Max retries hit—abort list")
        exit(1)
    data = response.json()
    page_data = data.get("conversations", [])  # Fixed: Use "conversations" key
    conversations.extend(page_data)
    cursor = data.get("next_cursor")
    print(f"ℹ️ Page {page} added {len(page_data)} convos | Total: {len(conversations)}")
    if not cursor:
        break
    page += 1
    time.sleep(0.5)  # Rate gentle

print(f"ℹ️ Fetched {len(conversations)} conversations total")

if not conversations:
    print("⚠️ Zero convos: UI History empty? Or re-link agent in Settings > API. Run scope_check.sh")
    exit(1)

# Step 2: Fetch details/transcript for first 3 (test; change to [:] for all 442+)
for i, conv in enumerate(conversations[:3]):
    try:
        conv_id = conv.get("conversation_id", conv.get("id", ""))  # Handle both keys
        detail_resp = requests.get(f"{BASE_URL}/convai/conversations/{conv_id}", headers=HEADERS)
        print(f"ℹ️ Detail {conv_id[:8]}...: {detail_resp.status_code}")
        if detail_resp.status_code == 200:
            details = detail_resp.json()
            transcript_data = {
                "conversation_id": conv_id,
                "title": conv.get("title", conv.get("call_summary_title", "")),
                "duration": conv.get("call_duration_secs", conv.get("duration", 0)),
                "created_at": conv.get("start_time_unix_secs", conv.get("created_at", "")),
                "transcript": details.get("transcript", details.get("content", "No transcript available - Enable Data Collection in UI Analysis tab"))
            }
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{transcripts_dir}/{conv_id}_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(transcript_data, f, indent=2)
            print(f"✅ Saved {conv_id[:8]}... to {filename} | Transcript len: {len(str(transcript_data['transcript']))}")
        else:
            print(f"⚠️ Detail {detail_resp.status_code} for {conv_id[:8]}...: {detail_resp.text[:100]} - Toggle Data Collection?")
    except Exception as e:
        print(f"⚠️ Fetch error for {conv['conversation_id'][:8] if 'conversation_id' in conv else 'unknown'}: {e}")

# Auto-sync to Git
os.system("python git_sync.py")
print("ℹ️ Git sync triggered—check repo for new JSONs")
