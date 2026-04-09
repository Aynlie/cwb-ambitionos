import os
import sys
import psycopg2
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Ensure the root directory is in the path for 'agents' import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

load_dotenv()

app = Flask(__name__)

# PostgreSQL Connection
def get_pg_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", 5432),
        sslmode="require"
    )

# Azure AI Search Client
search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
)

def get_all_tasks():
    """Fetch all tasks from PostgreSQL"""
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("SELECT task, owner, due_date, status, category, priority FROM tasks ORDER BY id ASC")
    tasks = []
    for row in cur.fetchall():
        tasks.append({
            "task": row[0],
            "owner": row[1],
            "due_date": row[2],
            "status": row[3],
            "category": row[4],
            "priority": row[5]
        })
    cur.close()
    conn.close()
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

@app.route("/changes")
def get_changes():
    """Fetch all change logs from PostgreSQL"""
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("SELECT task_name, field_changed, old_value, new_value, changed_at FROM change_logs ORDER BY changed_at DESC")
    changes = []
    for row in cur.fetchall():
        changes.append({
            "task_name": row[0],
            "field_changed": row[1],
            "old_value": row[2],
            "new_value": row[3],
            "changed_at": row[4].strftime("%Y-%m-%d %H:%M:%S") if row[4] else ""
        })
    cur.close()
    conn.close()
    return jsonify(changes)

@app.route("/search")
def search():
    """Search tasks using Azure AI Search"""
    q = request.args.get("q", "")
    if not q:
        return jsonify([])
    
    try:
        results = search_client.search(search_text=q)
        tasks = []
        for result in results:
            tasks.append({
                "task": result.get("task", ""),
                "owner": result.get("owner", "Jaymee"),
                "due_date": result.get("due_date", "TBD"),
                "status": result.get("status", "Not Started"),
                "category": result.get("category", "Admin"),
                "priority": result.get("priority", "Low")
            })
        return jsonify(tasks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sync", methods=["POST"])
def sync_data():
    """Trigger the change detection agent"""
    try:
        from agents.change_detection_agent import run_change_detection
        run_change_detection()
        return jsonify({"status": "success", "message": "Synchronization complete!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
