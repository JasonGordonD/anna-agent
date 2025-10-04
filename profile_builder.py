import requests
import json
from datetime import datetime

SUPABASE_URL = "https://qumhcrbukjhfwcsoxpyr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0.EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI"
SUPABASE_LOG_ENDPOINT = f"{SUPABASE_URL}/rest/v1/session_logs"

PROFILE_PATH = "billy_profile.txt"

def fetch_logs_from_supabase():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(SUPABASE_LOG_ENDPOINT + "?select=*", headers=headers)
    print("DEBUG STATUS CODE:", response.status_code)
    print("DEBUG RESPONSE TEXT:", response.text)
    if response.status_code == 200:
        return response.json()
    return []

def build_composite_summary(logs):
    if not logs:
        return "No session data available to summarize."

    summary = "## Long-Term Composite Profile\n\n"
    for i, log in enumerate(reversed(logs)):
        summary += f"### Session {i+1}:\n"
        summary += f"- Input: {log.get('user_input', '')}\n"
        summary += f"- Summary: {log.get('ai_summary', '')}\n"
        summary += f"- Trust: {log.get('trust_level', 'N/A')}, Anxiety: {log.get('anxiety_index', 'N/A')}, Edge: {log.get('edge_index', 'N/A')}\n\n"
    summary += "### Pattern Observations:\n- Identify emotional cycles, reinforcement triggers, submission patterns, and dominant shifts here.\n"
    return summary

def write_profile_file(summary_text):
    with open(PROFILE_PATH, "w") as f:
        f.write(summary_text)

def load_long_term_profile():
    try:
        with open(PROFILE_PATH, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "No long-term profile available yet."

def generate_long_term_profile():
    logs = fetch_logs_from_supabase()
    summary = build_composite_summary(logs)
    write_profile_file(summary)
    return summary

if __name__ == "__main__":
    final_summary = generate_long_term_profile()
    print(final_summary)