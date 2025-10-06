import requests
import json

# Canonized Agents Platform key for R/W scopes
AGENTS_KEY = "sk_0434e282b02f333781fb7568cb4f9cbbf4449442a1537d36"
BASE_URL = "https://api.elevenlabs.io/v1"
HEADERS = {"xi-api-key": AGENTS_KEY, "Content-Type": "application/json"}

agent_id = "agent_2901k6qjvk71e9cbftde9wzyt94n"

# Step 1: Dump agent config (scan for data_collection/transcripts_enabled)
try:
    resp = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=HEADERS)
    resp.raise_for_status()
    agent = resp.json()
    print("Agent Config Dump:")
    print(json.dumps(agent, indent=2))  # Full JSON: Look for "data_collection_items" or "transcripts_enabled"
except Exception as e:
    print(f"Agent GET fail: {e} - {resp.text if 'resp' in locals() else 'N/A'}")

# Step 2: Attempt agent PATCH to enable transcripts (add to data_collection_items)
try:
    # Fetch current to merge
    current_resp = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=HEADERS)
    current_agent = current_resp.json()
    current_items = current_agent.get("data_collection_items", [])
    if "transcript" not in current_items:
        current_items.append("transcript")
        payload = {"data_collection_items": current_items}
        update_resp = requests.patch(f"{BASE_URL}/agents/{agent_id}", headers=HEADERS, json=payload)
        update_resp.raise_for_status()
        print(f"\nToggle Success: Updated data_collection_items: {update_resp.json().get('data_collection_items')}")
    else:
        print("\nTranscript already enabled at agent level.")
except Exception as e:
    print(f"Agent PATCH fail (UI fallback needed): {e} - {update_resp.text if 'update_resp' in locals() else 'N/A'}")

# Step 3: Fallback /v1/convai/conversations check (metadata baseline)
try:
    convai_key = "1232ea6ab756"  # Canonized ConvAI key
    conv_headers = {"xi-api-key": convai_key, "Content-Type": "application/json"}
    conv_resp = requests.get(f"{BASE_URL}/convai/conversations", headers=conv_headers)
    conv_resp.raise_for_status()
    print(f"\nConvAI Metadata Baseline: {len(conv_resp.json())} conversations available.")
except Exception as e:
    print(f"ConvAI GET fail: {e}")
