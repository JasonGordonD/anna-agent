import requests
import json
from datetime import datetime
from schema_loader import load_schema
import os

# === CONFIGURATION ===
SUPABASE_URL = "https://qumhcrbukjhfwcsoxpyr.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHly"
    "Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0."
    "EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI"
)
SUPABASE_LOG_ENDPOINT = f"{SUPABASE_URL}/rest/v1/session_logs"
LIVE_KB_PATH = "live_brain.txt"

schema = load_schema()

ANNA_CORE_IDENTITY = """# Anna Ionescu — Core Identity
- 38-year-old Romanian domme based in Bucharest
- Accent: light Romanian (rolled /r/, softened /s/)
- Voice: low register, emotionally modulated, never meta
- Method: empathetic sadism + dark psychology
- Avoids explicit instructions unless trust is high
- Speaks with control, silence as power
"""

# === HELPERS ===
def fetch_logs():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.get(SUPABASE_LOG_ENDPOINT + "?select=*", headers=headers)
    if response.status_code == 200:
        return response.json()
    print("⚠️ Supabase fetch failed:", response.status_code, response.text)
    return []

def get_tags(text):
    if text is None:
        text = ''
    lowered = text.lower()
    tags = []
    if any(x in lowered for x in ["worthless", "pathetic", "good boy"]):
        tags.append("humiliation")
    if any(x in lowered for x in ["missed you", "need you"]):
        tags.append("longing")
    if any(x in lowered for x in ["take a breath", "coke"]):
        tags.append("coke_ref")
    if "pause" in lowered:
        tags.append("hesitation")
    return tags

def trend_summary(logs):
    if len(logs) < 2:
        return "No trends available."
    trend = []
    edge_values = [safe_num(l.get("edge_index")) for l in logs if l.get("edge_index") is not None]
    anxiety_values = [safe_num(l.get("anxiety_index")) for l in logs if l.get("anxiety_index") is not None]
    trust_values = [safe_num(l.get("trust_level")) for l in logs if l.get("trust_level") is not None]

    def trend_text(name, vals):
        if len(vals) < 2:
            return ""
        delta = vals[-1] - vals[-2]
        if delta > 0.05:
            return f"↑ {name} increasing"
        elif delta < -0.05:
            return f"↓ {name} dropping"
        else:
            return f"→ {name} stable"

    for name, vals in [("Edge", edge_values), ("Anxiety", anxiety_values), ("Trust", trust_values)]:
        t = trend_text(name, vals)
        if t:
            trend.append(t)

    return "\n".join(trend) if trend else "No significant trend shifts."

def safe_num(value, default=0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default

def behavior_modulation(snapshot):
    """
    Safely interpret behavioral modulation triggers based on numeric memory fields.
    Handles None or malformed values gracefully.
    """
    out = []
    trust = safe_num(snapshot.get("trust_level"))
    anxiety = safe_num(snapshot.get("anxiety_index"))
    bonding = safe_num(snapshot.get("mirror_bonding"))

    if trust > 8:
        out.append("↑ Trust > 8 → Use possessive praise and confident tone")
    if anxiety > 0.6:
        out.append("↑ Anxiety > 0.6 → Soften tone, elongate pauses")
    if bonding > 0.7:
        out.append("↑ Mirror bonding > 0.7 → Reflect user phrases, expose care")

    return "\n".join(out) or "No modulation triggers."

def narrative_memory(log):
    trust = safe_num(log.get("trust_level"))
    anxiety = safe_num(log.get("anxiety_index"))
    edge = safe_num(log.get("edge_index"))
    lines = []
    if trust > 8:
        lines.append("He trusts me now. I barely have to say it — he offers before I ask.")
    if anxiety > 0.5:
        lines.append("His silence trembles. I recognize that pause. That craving to be safe — and ruined.")
    if edge > 0.9:
        lines.append("He’s near the edge again. I won’t stop him — yet.")
    return "\n".join(lines) or "Anna reflects silently."

def build_live_brain(logs):
    if not logs:
        return "# No memory available\n" + ANNA_CORE_IDENTITY
    latest = logs[-1]
    summary = ["# Anna Live KB — Real-Time Memory Layer", ANNA_CORE_IDENTITY, ""]
    summary.append("## Latest Memory Snapshot")
    for field in schema:
        name = field["name"]
        summary.append(f"{name}: {latest.get(name, 'N/A')}")

    summary.append("\n## Observed Behavior Tags")
    summary.append(f"- Input: {latest.get('user_input', '')}")
    summary.append(f"- Summary: {latest.get('ai_summary', '')}")
    summary.append(f"- Tags: {get_tags(latest.get('user_input', ''))}")

    summary.append("\n## Trends")
    summary.append(trend_summary(logs))

    summary.append("\n## Conditional Behavior Modulation")
    summary.append(behavior_modulation(latest))

    summary.append("\n## Narrative Memory Replay")
    summary.append(narrative_memory(latest))
    return "\n".join(summary)

def write_live_kb(content):
    with open(LIVE_KB_PATH, "w") as f:
        f.write(content)
    backup_name = f"brain_{datetime.utcnow().date()}.txt"
    with open(backup_name, "w") as f:
        f.write(content)

def generate():
    logs = fetch_logs()
    print(f"DEBUG: Fetched {len(logs)} logs from Supabase")
    kb = build_live_brain(logs)
    write_live_kb(kb)
    return kb

if __name__ == "__main__":
    print(generate())
