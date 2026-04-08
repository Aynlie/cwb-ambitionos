import os
import csv
from dotenv import load_dotenv
from azure.data.tables import TableServiceClient

load_dotenv()

conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
table_service = TableServiceClient.from_connection_string(conn_str)
table_client = table_service.get_table_client("ambitionosdata")

tasks = list(table_client.list_entities())

with open("data/powerbi_export.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "Task", "Owner", "DueDate", 
        "Status", "Category", "Priority", "Source"
    ])
    writer.writeheader()
    for t in tasks:
        writer.writerow({
            "Task": t.get("Task", ""),
            "Owner": t.get("Owner", ""),
            "DueDate": t.get("DueDate", ""),
            "Status": t.get("Status", ""),
            "Category": t.get("Category", ""),
            "Priority": t.get("Priority", ""),
            "Source": t.get("Source", "")
        })

print(f"✅ Exported {len(tasks)} tasks to data/powerbi_export.csv!")
