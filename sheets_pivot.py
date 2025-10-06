from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import json

# Google Sheets setup (add your service account JSON path/key)
SHEET_ID = "YOUR_SHEET_ID"
SERVICE_ACCOUNT_FILE = "path/to/service_account.json"

def load_memory_from_sheets():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range="session_logs").execute()
    rows = result.get('values', [])
    if rows:
        # Parse rows to memory_blob (col 0: timestamp, col 1: user_input, etc.)
        return {'memory_blob': dict(zip(['trust_level', 'anxiety_index'], [float(rows[-1][4]), float(rows[-1][5])]))}
    return {}

if __name__ == "__main__":
    print(load_memory_from_sheets())
