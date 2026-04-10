import os
import sys
import psycopg2
from flask import Flask, render_template, jsonify, request, redirect, url_for
from dotenv import load_dotenv

# Ensure the root directory is in the path for 'agents' import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

load_dotenv()

app = Flask(__name__)

# ── Import user profiles module ──
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.user_profiles import save_profile, get_profile, setup_user_profiles_table

# Ensure the table exists on startup (safe — uses IF NOT EXISTS)
try:
    setup_user_profiles_table()
except Exception as _e:
    print(f"[WARN] Could not verify user_profiles table: {_e}")

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
    cur.execute("SELECT task, owner, due_date, status, category, priority, source, confidence, approval_status, dependency FROM tasks ORDER BY id ASC")
    tasks = []
    for row in cur.fetchall():
        tasks.append({
            "task": row[0],
            "owner": row[1],
            "due_date": row[2],
            "status": row[3],
            "category": row[4],
            "priority": row[5],
            "source": row[6],
            "confidence": row[7],
            "approval_status": row[8],
            "dependency": row[9]
        })
    cur.close()
    conn.close()
    return tasks

@app.route("/")
def dashboard():
    # ── Onboarding guard ──
    profile = get_profile()
    if profile is None:
        return redirect(url_for('onboarding'))

    all_tasks = get_all_tasks()
    dashboard_tasks = [t for t in all_tasks if t["approval_status"] != "Rejected"]
    high = [t for t in dashboard_tasks if t["priority"] == "High" and t["approval_status"] == "Approved"]
    in_progress = [t for t in dashboard_tasks if t["status"] == "In Progress" and t["approval_status"] == "Approved"]

    tab_config = profile.get("tab_config", {})
    user_name = profile.get("name", "")

    return render_template("index.html",
                         tasks=dashboard_tasks,
                         high_priority=high,
                         in_progress=in_progress,
                         tab_config=tab_config,
                         user_name=user_name)


@app.route("/onboarding")
def onboarding():
    """Show Amby welcome screen. Skip if user already onboarded."""
    profile = get_profile()
    if profile is not None:
        return redirect(url_for('dashboard'))
    return render_template("onboarding.html")


@app.route("/api/onboarding/complete", methods=["POST"])
def onboarding_complete():
    """Save profile + return tab_config"""
    data = request.json
    if not data or not data.get("name"):
        return jsonify({"error": "Name is required"}), 400
    try:
        tab_config = save_profile(data)
        return jsonify({"status": "success", "tab_config": tab_config})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/profile")
def api_profile():
    """Return current user profile and tab_config"""
    profile = get_profile()
    if profile is None:
        return jsonify({"onboarded": False}), 404
    return jsonify(profile)


@app.route("/onboarding/reset")
def onboarding_reset():
    """Dev-only: clear profile to re-trigger onboarding"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"), database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"), password=os.getenv("POSTGRES_PASSWORD"),
            port=os.getenv("POSTGRES_PORT", 5432), sslmode="require"
        )
        cur = conn.cursor()
        cur.execute("DELETE FROM user_profiles;")
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('onboarding'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

@app.route("/api/task_history/<path:task_name>")
def task_history(task_name):
    """Fetch change logs for a specific task"""
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT field_changed, old_value, new_value, changed_at 
            FROM change_logs 
            WHERE task_name = %s 
            ORDER BY changed_at DESC
        """, (task_name,))
        
        history = []
        for row in cur.fetchall():
            history.append({
                "field": row[0],
                "old": row[1],
                "new": row[2],
                "at": row[3].strftime("%Y-%m-%d %H:%M")
            })
        
        cur.close()
        conn.close()
        return jsonify(history)
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

@app.route("/api/task/approve", methods=["POST"])
def approve_task():
    """Approve a pending task"""
    data = request.json
    task_name = data.get("task")
    if not task_name:
        return jsonify({"error": "Task name required"}), 400
    
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        
        # 1. Update status
        cur.execute("UPDATE tasks SET approval_status = 'Approved' WHERE task = %s", (task_name,))
        
        # 2. Log changes
        cur.execute("""
            INSERT INTO change_logs (task_name, field_changed, old_value, new_value)
            VALUES (%s, 'approval_status', 'Pending', 'Approved')
        """, (task_name,))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success", "message": f"Task '{task_name}' approved!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/task/reject", methods=["POST"])
def reject_task():
    """Reject a task with a reason"""
    data = request.json
    task_name = data.get("task")
    reason = data.get("reason", "No reason provided")
    if not task_name:
        return jsonify({"error": "Task name required"}), 400
    
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        
        # 1. Update status
        cur.execute("UPDATE tasks SET approval_status = 'Rejected' WHERE task = %s", (task_name,))
        
        # 2. Log rejection with reason
        cur.execute("""
            INSERT INTO change_logs (task_name, field_changed, old_value, new_value)
            VALUES (%s, 'rejected_with_reason', 'Pending', %s)
        """, (task_name, reason))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success", "message": f"Task '{task_name}' rejected."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
