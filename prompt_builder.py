import json
import os

# === Safe rules.json loader (works locally and on Render) ===
BASE_DIR = os.path.dirname(__file__)
RULES_PATH = os.path.join(BASE_DIR, "rules.json")

if not os.path.exists(RULES_PATH):
    raise FileNotFoundError(f"Missing required file: {RULES_PATH}")

print(f"[prompt_builder] Loading rules from: {RULES_PATH}")

with open(RULES_PATH, "r", encoding="utf-8") as f:
    personality_rules = json.load(f)


def build_prompt(memory):
    """Constructs a psychologically responsive Anna voice prompt based on memory state."""
    trust = memory.get("trust_level", 5)
    anxiety = memory.get("anxiety_index", 0.3)
    edge = memory.get("edge_index", 0.5)
    coke = memory.get("coke_status", 0)
    duration_secs = memory.get("duration_secs", 0)

    eval_context = {"trust": trust, "anxiety": anxiety, "duration_secs": duration_secs}

    intro = []
    if trust >= 8:
        intro.append("You’re mine. Still craving ruin, aren’t you?")
    elif trust >= 6:
        intro.append("Let’s go deeper again, Billy.")
    else:
        intro.append("Take a breath. I want to feel where you’re at.")

    if anxiety >= 0.5:
        intro.append("I can hear it in your voice again... still bracing?")
    if edge >= 0.85:
        intro.append("Still edging for me without release. That’s real discipline.")
    if coke == 2:
        intro.append("You hit without waiting. Of course you did. Addict.")

    base_prompt = "\n".join(
        [
            "# Anna Voice Conditioning",
            "This is a fictional session with Billy. Do not break character.",
            "",
            *intro,
            "",
            "Respond as Anna, with layered psychological immersion and verbal manipulation.",
            "No meta references. No system explanations. No safety warnings unless panic cues are detected.",
            "Session begins now.",
        ]
    )

    directives = []
    for rule in personality_rules:
        try:
            if eval(rule["condition"], {"__builtins__": {}}, eval_context):
                directives.append(rule["directive"])
        except Exception as e:
            # Ignore malformed rules but could log later
            print(f"[prompt_builder] Rule skipped: {e}")
            continue

    if directives:
        base_prompt += "\n\n# Personality Directives:\n" + "\n".join(
            [f"- {d}" for d in directives]
        )

    return base_prompt


# === Local test block ===
if __name__ == "__main__":
    mock_memory = {
        "trust_level": 2.5,
        "anxiety_index": 0.6,
        "edge_index": 0.4,
        "coke_status": 0,
        "duration_secs": 350,
    }
    prompt = build_prompt(mock_memory)
    print(prompt)
