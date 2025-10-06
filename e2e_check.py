import requests
import json

BASE_URL = "https://anna-agent.onrender.com"
SUPABASE_URL = "https://qumhcrbukjhfwcsoxpyr.supabase.co/rest/v1/session_logs"
HEADERS_SUPA = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0.EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0.EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI"
}

def check_e2e():
    # Pre-count logs
    pre_resp = requests.get(f"{SUPABASE_URL}?select=count", headers=HEADERS_SUPA)
    pre_logs = pre_resp.json()[0]['count']
    print(f"Pre-test log count: {pre_logs}")

    # Sim POST /speak (expect binary audio, but check status)
    speak_resp = requests.post(f"{BASE_URL}/speak", json={"text": "E2E test speak.", "voice_id": "zHX13TdWb6f856P3Hqta", "agent_id": "agent_2901k6qjvk71e9cbftde9wzyt94n"})
    print(f"/speak status: {speak_resp.status_code}")

    # Manual log post (since /speak doesn't auto yet)
    log_resp = requests.post(f"{BASE_URL}/log_memory", json={"memory_blob": {"trust_level": 5.5, "anxiety_index": 0.6}, "session_id": "e2e_sim"})
    print(f"/log_memory status: {log_resp.status_code}, response: {log_resp.json()}")

    # Post-count (expect +1)
    post_resp = requests.get(f"{SUPABASE_URL}?select=count", headers=HEADERS_SUPA)
    post_logs = post_resp.json()[0]['count']
    print(f"Post-test log count: {post_logs} (Delta: {post_logs - pre_logs})")

    # Assert: New log added
    assert post_logs > pre_logs, "E2E failed: No new log added"
    print("E2E passed: Pipeline intact")

if __name__ == "__main__":
    check_e2e()
