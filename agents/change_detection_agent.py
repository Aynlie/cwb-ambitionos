import os
import sys
import csv
import json
import requests
import psycopg2
import anthropic
from datetime import datetime
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.data.tables import TableServiceClient

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# ─────────────────────────────────────────
# CLIENTS
# ─────────────────────────────────────────
def get_pg_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", 5432),
        sslmode="require"
    )

# Azure AI Search client
search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
)

# Azure Table Storage client
table_service = TableServiceClient.from_connection_string(
    os.getenv("AZURE_STORAGE_CONNECTION_STRING")
)
table_client = table_service.get_table_client("ambitionosdata")

# Anthropic Claude client
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def normalize(value):
    """Normalize values for robust comparison: strip whitespace and lowercase"""
    if value is None or str(value).strip().lower() in ["none", "", "tbd"]:
        return "tbd"
    return str(value).strip().lower()


def map_task_data(data, source_type):
    """
    Unify field names from different sources into a standard format:
    task, owner, due_date, status, priority, category, source
    """
    if source_type == "csv":
        return {
            "task": data.get("Task", ""),
            "owner": data.get("Owner", "Jaymee"),
            "due_date": data.get("Due Date", "TBD"),
            "status": data.get("Status", "Not Started"),
            "priority": data.get("Priority", "Low"),
            "category": data.get("Category", "Admin"),
            "source": data.get("Source", "csv_baseline")
        }
    elif source_type == "table_storage":
        return {
            "task": data.get("Task", ""),
            "owner": data.get("Owner", "Jaymee"),
            "due_date": data.get("DueDate", "TBD"),
            "status": data.get("Status", "Not Started"),
            "priority": data.get("Priority", "Low"),
            "category": data.get("Category", "Admin"),
            "source": data.get("Source", "table_storage")
        }
    elif source_type == "postgres":
        return {
            "task": data.get("task", ""),
            "owner": data.get("owner", "Jaymee"),
            "due_date": data.get("due_date", "TBD"),
            "status": data.get("status", "Not Started"),
            "priority": data.get("priority", "Low"),
            "category": data.get("category", "Admin"),
            "source": data.get("source", "postgres")
        }
    return data


def log_change(cur, task_name, field_changed, old_value, new_value):
    """Insert a record into the change_logs table"""
    cur.execute("""
        INSERT INTO change_logs (task_name, field_changed, old_value, new_value)
        VALUES (%s, %s, %s, %s)
    """, (task_name, field_changed, str(old_value), str(new_value)))


def sync_to_search(task: dict):
    """Sync a single updated task to Azure AI Search"""
    import base64
    task_name = task["task"]
    owner = task.get("owner", "Jaymee")
    
    # Unified ID generation: base64(task_name_owner) 
    # Must match search_agent.py to prevent duplicates
    combined = f"{task_name}_{owner}".strip().lower()
    doc_id = base64.urlsafe_b64encode(combined.encode('utf-8')).decode('utf-8').rstrip('=')

    doc = {
        "id": doc_id,
        "task": task_name,
        "owner": task.get("owner", "Jaymee"),
        "due_date": task.get("due_date", "TBD"),
        "status": task.get("status", "Not Started"),
        "category": task.get("category", "Admin"),
        "priority": task.get("priority", "Low"),
        "source": task.get("source", "change_detection_agent"),
    }
    try:
        results = search_client.upload_documents([doc])
        if results[0].succeeded:
            print(f"  [SEARCH] Index updated: {task['task']}")
        else:
            print(f"  [WARN] Search sync failed: {task['task']}")
    except Exception as e:
        print(f"  [WARN] Search error: {e}")


def trigger_power_automate(task_name, changes, priority):
    """Trigger Power Automate flow for high priority changes"""
    url = os.getenv("POWER_AUTOMATE_URL")
    if not url:
        print("  [WARN] POWER_AUTOMATE_URL not set -- skipping notification")
        return

    payload = {
        "task": task_name,
        "priority": priority,
        "changes": changes,
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"HIGH PRIORITY task changed: {task_name}\nChanges: {json.dumps(changes)}"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code in [200, 202]:
            print(f"  [EMAIL] Power Automate triggered for: {task_name}")
        else:
            print(f"  [WARN] Power Automate responded: {response.status_code}")
    except Exception as e:
        print(f"  [WARN] Power Automate error: {e}")


def get_claude_summary(all_changes: list, new_tasks: list) -> str:
    """Use Claude AI to generate a smart summary of all detected changes"""
    if not all_changes and not new_tasks:
        return "No changes detected -- everything is up to date!"

    changes_text = json.dumps({
        "new_tasks": new_tasks,
        "updated_tasks": all_changes
    }, indent=2)

    message = claude_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": f"""You are AmbitionOS, a smart task tracking assistant for Jaymee, 
a BS Cybersecurity student at Holy Angel University in the Philippines.

Here are the task changes detected in her system:
{changes_text}

Write a short, friendly summary (3-5 sentences) of:
1. What changed and why it matters
2. Any urgent items she should focus on
3. A motivating closing line

Keep it concise, warm, and actionable. Use emojis sparingly."""
            }
        ]
    )
    return message.content[0].text


# ─────────────────────────────────────────
# LOAD DATA SOURCES
# ─────────────────────────────────────────
def load_from_postgres():
    """Fetch current tasks from PostgreSQL"""
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("SELECT task, owner, due_date, status, priority, category, source FROM tasks")
    old_tasks = {}
    for row in cur.fetchall():
        task, owner, due_date, status, priority, category, source = row
        task_data = {
            "task": task,
            "owner": owner,
            "due_date": due_date,
            "status": status,
            "priority": priority,
            "category": category,
            "source": source
        }
        mapped = map_task_data(task_data, "postgres")
        old_tasks[normalize(task)] = mapped
    cur.close()
    conn.close()
    return old_tasks


def load_from_table_storage():
    """Fetch tasks from Azure Table Storage"""
    print("[CLOUD] Loading tasks from Azure Table Storage...")
    entities = list(table_client.list_entities())
    tasks = {}
    for entity in entities:
        if entity.get("PartitionKey") == "tasks":
            mapped = map_task_data(entity, "table_storage")
            tasks[normalize(mapped["task"])] = mapped
    print(f"  [OK] Loaded {len(tasks)} tasks from Table Storage")
    return tasks


def load_from_csv(path="data/task_tracker_baseline.csv"):
    """Fetch tasks from CSV"""
    tasks = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapped = map_task_data(row, "csv")
            tasks[normalize(mapped["task"])] = mapped
    print(f"  [OK] Loaded {len(tasks)} tasks from CSV")
    return tasks


# ─────────────────────────────────────────
# MAIN DETECTION LOGIC
# ─────────────────────────────────────────
def run_change_detection():
    print("[INFO] Running AmbitionOS Change Detection Agent...\n")

    conn = get_pg_connection()
    cur = conn.cursor()

    pg_tasks = load_from_postgres()
    table_storage_tasks = load_from_table_storage()
    csv_tasks = load_from_csv()

    # Merge Logic (1st: Table Storage, 2nd: CSV)
    all_new_tasks = csv_tasks.copy()
    all_new_tasks.update(table_storage_tasks)

    changes_log = []
    new_tasks_log = []
    changes_detected = 0
    new_tasks_added = 0

    print(f"\n[COMPARE] PG has {len(pg_tasks)} tasks, merged sources have {len(all_new_tasks)} tasks\n")

    for task_id, new_task in all_new_tasks.items():
        task_name = new_task["task"]

        # ── NEW TASK ──
        if task_id not in pg_tasks:
            print(f"[NEW] TASK: {task_name}")
            cur.execute("""
                INSERT INTO tasks (task, owner, due_date, status, category, priority, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (task) DO NOTHING
            """, (
                task_name,
                new_task["owner"],
                new_task["due_date"],
                new_task["status"],
                new_task["category"],
                new_task["priority"],
                new_task["source"]
            ))
            log_change(cur, task_name, "new_task", "None", new_task["status"])
            sync_to_search(new_task)
            new_tasks_log.append(task_name)
            new_tasks_added += 1
            changes_detected += 1

        # ── EXISTING TASK — CHECK FOR CHANGES ──
        else:
            old = pg_tasks[task_id]
            updated_fields = {}
            fields_to_check = ["due_date", "status", "priority", "category"]

            for field in fields_to_check:
                old_val = old.get(field)
                new_val = new_task.get(field)
                
                norm_old = normalize(old_val)
                norm_new = normalize(new_val)
                
                if norm_old != norm_new:
                    print(f"  [DIFF] {field} for '{task_name}': '{norm_old}' -> '{norm_new}'")
                    log_change(cur, task_name, field, old_val, new_val)
                    updated_fields[field] = {"from": old_val, "to": new_val}
                    changes_detected += 1

            if updated_fields:
                print(f"[UPDATED] {task_name}")
                for field, change in updated_fields.items():
                    print(f"   {field}: '{change['from']}' -> '{change['to']}'")

                # Update PostgreSQL
                for field, change in updated_fields.items():
                    cur.execute(
                        f"UPDATE tasks SET {field} = %s WHERE task = %s",
                        (change["to"], task_name)
                    )

                # Sync to Azure AI Search
                sync_to_search(new_task)

                # Trigger Power Automate for high priority changes
                if normalize(new_task.get("priority")) == "high" or normalize(old.get("priority")) == "high":
                    trigger_power_automate(task_name, updated_fields, new_task.get("priority", "High"))

                changes_log.append({
                    "task": task_name,
                    "changes": updated_fields,
                    "priority": new_task.get("priority", "Low")
                })

    conn.commit()
    cur.close()
    conn.close()

    # ── CLAUDE AI SUMMARY ──
    print("\n" + "="*50)
    print("[AI] CLAUDE AI SUMMARY")
    print("="*50)
    try:
        summary = get_claude_summary(changes_log, new_tasks_log)
        print(summary)
    except Exception as e:
        print(f"  [WARN] Claude AI summary skipped: {e}")

    # ── FINAL REPORT ──
    print("\n" + "="*50)
    print("[DONE] Change Detection Complete!")
    print(f"   - {new_tasks_added} new tasks added")
    print(f"   - {len(changes_log)} tasks updated")
    print(f"   - {changes_detected} total changes logged to PostgreSQL")
    print(f"   - Azure AI Search synced")
    print("="*50)


if __name__ == "__main__":
    run_change_detection()