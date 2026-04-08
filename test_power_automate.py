import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("POWER_AUTOMATE_URL")

payload = {
    "task_name": "Apply MLSA",
    "field_changed": "Status",
    "old_value": "Not Started",
    "new_value": "In Progress",
    "changed_at": "2026-04-08"
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
if response.status_code == 202:
    print("✅ Power Automate flow triggered successfully!")
    print("📧 Check your HAU email for approval request!")
else:
    print(f"❌ Error: {response.text}")
