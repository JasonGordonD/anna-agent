import json

# Load personality rules from JSON (array of {"condition": str, "directive": str})
with open('rules.json', 'r') as f:
    personality_rules = json.load(f)

def build_prompt(memory):
    trust = memory.get("trust_level", 5)
    anxiety = memory.get("anxiety_index", 0.3)
    edge = memory.get("edge_index", 0.5)
    coke = memory.get("coke_status", 0)
    duration_secs = memory.get("duration_secs", 0)  # Added for rule support

    # Make schema vars available for eval() in rules (aligned to rule condition names)
    eval_context = {
        'trust': trust,
        'anxiety': anxiety,
        'duration_secs': duration_secs
    }

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

    # Base prompt assembly
    base_prompt = "\n".join([
        "# Anna Voice Conditioning",
        "This is a fictional session with Billy. Do not break character.",
        "",
        *intro,
        "",
        "Respond as Anna, with layered psychological immersion and verbal manipulation.",
        "No meta references. No system explanations. No safety warnings unless panic cues are detected.",
        "Session begins now."
    ])

    # Apply personality rules dynamically via eval() on conditions
    directives = []
    for rule in personality_rules:
        try:
            if eval(rule['condition'], {"__builtins__": {}}, eval_context):
                directives.append(rule['directive'])
        except Exception:
            # Silent skip on malformed rule (log in prod if needed)
            pass

    # Append rules as directive lines if any
    if directives:
        base_prompt += "\n\n# Personality Directives:\n" + "\n".join([f"- {dir}" for dir in directives])

    return base_prompt

# Local test block (run with: python prompt_builder.py)
if __name__ == "__main__":
    mock_memory = {
        'trust_level': 2.5,     # low trust (triggers amplify empathy)
        'anxiety_index': 0.6,   # mid anxiety (no >7 trigger)
        'edge_index': 0.4,      # low edge
        'coke_status': 0,       # low coke
        'duration_secs': 350    # high duration (triggers deepen)
    }
    prompt = build_prompt(mock_memory)
    print(prompt)  # Expect: Base with low-trust intro, plus directives "- Amplify empathy: ...", "- Deepen rapport: ..."
