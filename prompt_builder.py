import json

# Load personality rules (existing personality_rules.json in project root)
with open('personality_rules.json', 'r') as f:
    personality_rules = json.load(f)

def build_prompt(memory):
    trust = memory.get("trust_level", 5)
    anxiety = memory.get("anxiety_index", 0.3)
    edge = memory.get("edge_index", 0.5)
    coke = memory.get("coke_status", 0)

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

    # Apply personality rules conditionally (post-base for layered directives)
    rules_modifiers = []
    
    # Map trust_level
    if trust < 6:
        rules_modifiers.extend(personality_rules["trust_level"]["low"])
    else:
        rules_modifiers.extend(personality_rules["trust_level"]["high"])
    
    # Map anxiety_index
    if anxiety < 0.5:
        rules_modifiers.extend(personality_rules["anxiety_index"]["low"])
    else:
        rules_modifiers.extend(personality_rules["anxiety_index"]["high"])
    
    # Map edge_index
    if edge < 0.85:
        rules_modifiers.extend(personality_rules["edge_index"]["low"])
    else:
        rules_modifiers.extend(personality_rules["edge_index"]["high"])
    
    # Map coke_status (treat 0/1 as low, 2 as high)
    if coke == 2:
        # No coke-specific rule in JSON yet; extend if added later
        pass
    else:
        # Placeholder for future; currently no low/high for coke in JSON
        pass

    # Append rules as directive lines if any
    if rules_modifiers:
        base_prompt += "\n\n# Personality Directives:\n" + "\n".join([f"- {mod}" for mod in rules_modifiers])

    return base_prompt

# Local test block (run with: python prompt_builder.py)
if __name__ == "__main__":
    mock_memory = {
        'trust_level': 7,       # high trust
        'anxiety_index': 0.6,   # high anxiety
        'edge_index': 0.4,      # low edge
        'coke_status': 0        # low coke
    }
    prompt = build_prompt(mock_memory)
    print(prompt)  # Expect: Base with intro/anxiety line, plus directives like "- speak softly", "- include ownership phrases", "- offer reassurance", "- lower volume", "- tease slower", "- delay escalation"
