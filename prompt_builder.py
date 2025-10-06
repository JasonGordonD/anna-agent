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
    if user_id == 'rami':
        persona_path = os.path.join(BASE_DIR, "rami_persona.json")
        try:
            with open(persona_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("WARNING: rami_persona.json missing; using default for rami.")
            return {}
    # Default for billy/anna_self (Anna core + rules.json handles)
    return {}


def build_prompt(memory, user_id='billy'):
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
        intro.append(f"Let’s go deeper again, {user_id.title()}.")
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
            "This is a fictional session with {user_id}. Do not break character.".format(user_id=user_id),
            "",
            *intro,
            "",
            "Respond as Anna, with layered psychological immersion and verbal manipulation.",
            "No meta references. No system explanations. No safety warnings unless panic cues are detected.",
            "Session begins now.",
        ]
    )

    # Load and inject persona if available
    persona = load_persona(user_id)
    persona_inject = ""
    if persona:
        persona_inject = f"\nUser Persona Context: {persona.get('background', '')}\nKey Traits: {', '.join(persona.get('personality_traits', []))}\nSpeaking Style: {persona.get('speaking_style', '')}\nAdapt responses to this persona dynamically."

    base_prompt += persona_inject

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
    prompt = build_prompt(mock_memory, user_id='rami')
    print(prompt)
