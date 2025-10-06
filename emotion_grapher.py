import requests
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np

# Supabase config — using your actual keys and endpoint
SUPABASE_URL = "https://qumhcrbukjhfwcsoxpyr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bWhjcmJ1a2poZndjc294cHlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk1ODE5MjIsImV4cCI6MjA3NTE1NzkyMn0.EYOMJ7kEZ3uvkIqcJhDVS3PCrlHx2JrkFTP6OuVg3PI"
SUPABASE_LOG_ENDPOINT = f"{SUPABASE_URL}/rest/v1/session_logs"

def fetch_logs():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(SUPABASE_LOG_ENDPOINT + "?select=*", headers=headers)
    return response.json()

def get_coke_streaks(logs):
    streaks = []
    streak = 0
    for log in reversed(logs):
        status = int(log.get("coke_status") or 0)
        if status >= 1:
            streak += 1
        else:
            streak = 0
        streaks.append(streak)
    return list(reversed(streaks))

def plot_emotions(logs):
    sessions = list(range(1, len(logs)+1))
    trust = [log.get("trust_level", None) for log in logs]
    anxiety = [log.get("anxiety_index", None) for log in logs]
    edge = [log.get("edge_index", None) for log in logs]
    coke = [int(log.get("coke_status") or 0) for log in logs]
    streaks = get_coke_streaks(logs)

    fig, axs = plt.subplots(4, 1, figsize=(10, 12), sharex=True)

    axs[0].plot(sessions, trust, marker='o', color='green')
    axs[0].set_title("Trust Level")

    axs[1].scatter(sessions, anxiety, c=anxiety, cmap="YlOrRd", s=80)
    axs[1].set_title("Anxiety Index (heatmap color)")

    axs[2].plot(sessions, edge, marker='o', color='purple')
    axs[2].set_title("Edge Index")

    axs[3].bar(sessions, coke, color='gray', alpha=0.7, label="Coke Status")
    axs[3].plot(sessions, streaks, color='red', label="Coke Streak")
    axs[3].legend()
    axs[3].set_title("Coke Status & Streak")

    plt.xlabel("Session")
    plt.tight_layout()
    plt.savefig("emotion_metrics_combined.png")
    plt.show()

if __name__ == "__main__":
    logs = fetch_logs()
    plot_emotions(logs)
