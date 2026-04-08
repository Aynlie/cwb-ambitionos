from flask import Flask, render_template, jsonify
import os
from dotenv import load_dotenv
from azure.data.tables import TableServiceClient

load_dotenv()

app = Flask(__name__)

# Azure Table Storage
table_service = TableServiceClient.from_connection_string(
    os.getenv("AZURE_STORAGE_CONNECTION_STRING")
)
table_client = table_service.get_table_client("ambitionosdata")

def get_all_tasks():
    """Fetch all tasks from Azure Table Storage"""
    tasks = []
    for entity in table_client.list_entities():
        tasks.append({
            "task": entity.get("Task", ""),
            "owner": entity.get("Owner", ""),
            "due_date": entity.get("DueDate", ""),
            "status": entity.get("Status", ""),
            "category": entity.get("Category", ""),
            "priority": entity.get("Priority", "")
        })
    return tasks

@app.route("/")
def dashboard():
    tasks = get_all_tasks()
    high = [t for t in tasks if t["priority"] == "High"]
    in_progress = [t for t in tasks if t["status"] == "In Progress"]
    return render_template("index.html", 
                         tasks=tasks,
                         high_priority=high,
                         in_progress=in_progress)

@app.route("/api/tasks")
def api_tasks():
    return jsonify(get_all_tasks())

if __name__ == "__main__":
    app.run(debug=True)
