def build_prompt(memory):
    return f"""
# Memory Snapshot
trust_level: {memory['trust_level']}
session_count: {memory['session_count']}
anxiety_index: {memory['anxiety_index']}
coke_status: {memory['coke_status']}

# Anna v1.1 Core Logic
(Insert shortened system prompt here...)
"""
