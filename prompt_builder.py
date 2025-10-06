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

def load_persona(user_id='billy'):
    """Load user-specific persona for prompt injection."""
    persona_map = {
        "billy": "billy_persona.json",
        "rami": "rami_persona.json",
        "anna_self": "anna_self_persona.json",
        "ansp": "anna_self_persona.json"  # same context for analytical self
    }
    persona_file = persona_map.get(user_id)
    if not persona_file:
        return {}

    persona_path = os.path.join(BASE_DIR, persona_file)
    try:
        with open(persona_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[prompt_builder] Missing persona file for {user_id}; using defaults.")
        return {}

def build_prompt(memory, user_id='billy'):
    """Constructs an Anna voice prompt dynamically based on memory + persona."""
    trust = memory.get("trust_level", 5)
    anxiety = memory.get("anxiety_index", 0.3)
    edge = memory.get("edge_index", 0.5)
    coke = memory.get("coke_status", 0)
    duration_secs = memory.get("duration_secs", 0)

    eval_context = {"trust": trust, "anxiety": anxiety, "duration_secs": duration_secs}
    visible_user_id = "anna" if user_id in ["anna_self", "ansp"] else user_id

    # === Intro logic ===
    intro = []
    if trust >= 8:
        intro.append("You’re mine. Still craving ruin, aren’t you?")
    elif trust >= 6:
        intro.append(f"Let’s go deeper again, {visible_user_id.title()}.")
    else:
        intro.append("Take a breath. I want to feel where you’re at.")

    # === Emotional cues ===
    if user_id not in ["anna_self", "ansp"]:  # skip tension cues for introspection
        if anxiety >= 0.5:
            intro.append("I can hear it in your voice again... still bracing?")
        if edge >= 0.85:
            intro.append("Still edging for me without release. That’s real discipline.")
        if coke == 2:
            intro.append("You hit without waiting. Of course you did. Addict.")
    else:
        intro.append("Focus on awareness, not control. Observe without judgment.")

    # === Adjusted manipulation clause ===
    if user_id in ["anna_self", "ansp"]:
        manipulation_clause = (
            "Respond as Anna, calmly and introspectively, focused on understanding and clarity rather than control."
        )
    else:
        manipulation_clause = (
            "Respond as Anna, with layered psychological immersion and verbal manipulation."
        )

    base_prompt = "\n".join([
        "# Anna Voice Conditioning",
        f"This is a fictional session with {visible_user_id}. Do not break character.",
        "",
        *intro,
        "",
        manipulation_clause,
        "No meta references. No system explanations. No safety warnings unless panic cues are detected.",
        "Session begins now.",
    ])

    # === Persona injection ===
    persona = load_persona(user_id)
    if persona:
        persona_inject = (
            f"\nUser Persona Context: {persona.get('background', '')}"
            f"\nKey Traits: {', '.join(persona.get('personality_traits', []))}"
            f"\nSpeaking Style: {persona.get('speaking_style', '')}"
            "\nAdapt responses to this persona dynamically."
        )
        base_prompt += persona_inject

    # === Conditional personality directives ===
    directives = []
    for rule in personality_rules:
        try:
            if eval(rule["condition"], {"__builtins__": {}}, eval_context):
                directives.append(rule["directive"])
        except Exception as e:
            print(f"[prompt_builder] Rule skipped: {e}")
            continue

    if directives and user_id not in ["anna_self", "ansp"]:
        base_prompt += "\n\n# Personality Directives:\n" + "\n".join(
            [f"- {d}" for d in directives]
        )

    return base_prompt

# === Local test block ===
if __name__ == "__main__":
    mock_memory = {
        "trust_level": 8.2,
        "anxiety_index": 0.4,
        "edge_index": 0.91,
        "coke_status": 2,
        "duration_secs": 350,
    }
    print(build_prompt(mock_memory, user_id='anna_self'))
