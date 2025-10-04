import requests
import matplotlib.pyplot as plt

SUPABASE_URL = "https://qumhcrbukjhfwcsoxpyr.supabase.co"
SUPABASE_KEY = "your_full_key_here"  # Same one you’ve used

def fetch_logs():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    url = f"{SUPABASE_URL}/rest/v1/session_logs?select=*"
    response = requests.get(url, headers=headers)
    return response.json()

def plot_metric(metric):
    logs = fetch_logs()
    values = [log[metric] for log in logs if log[metric] is not None]
    sessions = list(range(1, len(values)+1))

    plt.figure(figsize=(8,4))
    plt.plot(sessions, values, marker="o")
    plt.title(f"{metric} Over Time")
    plt.xlabel("Session")
    plt.ylabel(metric.capitalize())
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    plot_metric("trust_level")
    plot_metric("anxiety_index")
    plot_metric("edge_index")
