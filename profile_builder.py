import requests
import json
from datetime import datetime
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qumhcrbukjhfwcsoxpyr.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
SUPABASE_LOG_ENDPOINT = f"{SUPABASE_URL}/rest/v1/session_logs"
LIVE_KB_BASE = "live_brain_{user}.txt"

# === Load schema dynamically (unchanged) ===
def load_schema():
    schema = [
        {"name": "trust_level", "type": "float"},
        {"name": "anxiety_index", "type": "float"},
        {"name": "edge_index", "type": "float"},
        {"name": "coke_status", "type": "int"},
        {"name": "session_count", "type": "int"},
    ]
    return schema

def safe_num(value, default=0):
    try:
        return float(value)
    except Exception:
        return default

# === Fetch logs from Supabase per user ===
def fetch_logs(user_id='billy'):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    url = f"{SUPABASE_LOG_ENDPOINT}?select=*&user_id=eq.{user_id}&order=timestamp.asc"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
        print(f"[profile_builder] Fetch failed {r.status_code}: {r.text}")
    except Exception as e:
        print(f"[profile_builder] Error fetching logs for {user_id}: {e}")
    return []

# === Trend summarization ===
def trend_summary(logs):
    if len(logs) < 2:
        return "No trends available."
    trend = []
    trust = [safe_num(l.get("trust_level")) for l in logs]
    anxiety = [safe_num(l.get("anxiety_index")) for l in logs]
    edge = [safe_num(l.get("edge_index")) for l in logs]

    def compare(name, vals):
        if len(vals) < 2: return ""
        delta = vals[-1] - vals[-2]
        if delta > 0.05: return f"↑ {name} increasing"
        if delta < -0.05: return f"↓ {name} decreasing"
        return f"→ {name} stable"

    for name, vals in [("Trust", trust), ("Anxiety", anxiety), ("Edge", edge)]:
        msg = compare(name, vals)
        if msg: trend.append(msg)
    return "\n".join(trend)

# === Build live brain text ===
def build_live_brain(user_id='billy', logs=None):
    if logs is None:
        logs = fetch_logs(user_id)
    if not logs:
        return f"# No memory available for {user_id}\n"
    latest = logs[-1]
    schema = load_schema()
    lines = [f"# Anna Live KB — {user_id.title()} Persona", ""]
    for fdef in schema:
        name = fdef["name"]
        lines.append(f"{name}: {latest.get(name, 'N/A')}")
    lines.append("\n## Trend Summary")
    lines.append(trend_summary(logs))
    return "\n".join(lines)

# === Write KB file ===
def write_live_kb(content, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[profile_builder] Wrote KB file: {filename}")

# === Main entry ===
def generate(user_id='billy'):
    logs = fetch_logs(user_id)
    kb_text = build_live_brain(user_id, logs)
    filename = LIVE_KB_BASE.format(user=user_id)
    write_live_kb(kb_text, filename)
    return kb_text

if __name__ == "__main__":
    print(generate("billy"))
    print(generate("rami"))
    print(generate("anna_self"))
