import os
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
def log_change(cur, task_name, field_changed, old_value, new_value):
    """Insert a record into the change_logs table"""
    cur.execute("""
        INSERT INTO change_logs (task_name, field_changed, old_value, new_value)
        VALUES (%s, %s, %s, %s)
    """, (task_name, field_changed, str(old_value), str(new_value)))


def sync_to_search(task: dict):
    """Sync a single updated task to Azure AI Search"""
    doc = {
        "id": task["task"].replace(" ", "_")[:50],
        "task": task["task"],
        "owner": task.get("owner", "Jaymee"),
        "due_date": task.get("due_date", task.get("Due Date", "TBD")),
        "status": task.get("status", task.get("Status", "Not Started")),
        "category": task.get("category", task.get("Category", "Admin")),
        "priority": task.get("priority", task.get("Priority", "Low")),
        "source": task.get("source", "change_detection_agent"),
    }
    try:
        results = search_client.upload_documents([doc])
        if results[0].succeeded:
            print(f"  🔍 Search index updated: {task['task']}")
        else:
            print(f"  ⚠️  Search sync failed: {task['task']}")
    except Exception as e:
        print(f"  ⚠️  Search error: {e}")


def trigger_power_automate(task_name, changes, priority):
    """Trigger Power Automate flow for high priority changes"""
    url = os.getenv("POWER_AUTOMATE_URL")
    if not url:
        print("  ⚠️  POWER_AUTOMATE_URL not set — skipping notification")
        return

    payload = {
        "task": task_name,
        "priority": priority,
        "changes": changes,
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"🚨 High priority task changed: {task_name}\nChanges: {json.dumps(changes)}"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code in [200, 202]:
            print(f"  📧 Power Automate triggered for: {task_name}")
        else:
            print(f"  ⚠️  Power Automate responded: {response.status_code}")
    except Exception as e:
        print(f"  ⚠️  Power Automate error: {e}")


def get_claude_summary(all_changes: list, new_tasks: list) -> str:
    """Use Claude AI to generate a smart summary of all detected changes"""
    if not all_changes and not new_tasks:
        return "No changes detected — everything is up to date! ✅"

    changes_text = json.dumps({
        "new_tasks": new_tasks,
        "updated_tasks": all_changes
    }, indent=2)

    message = claude_client.messages.create(
        model="claude-opus-4-5",
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
    cur.execute("SELECT task, due_date, status, priority, category FROM tasks")
    old_tasks = {}
    for row in cur.fetchall():
        task_name, due_date, status, priority, category = row
        old_tasks[task_name] = {
            "Due Date": str(due_date) if due_date else "TBD",
            "Status": status,
            "Priority": priority,
            "Category": category
        }
    cur.close()
    conn.close()
    return old_tasks


def load_from_table_storage():
    """Fetch tasks from Azure Table Storage"""
    print("☁️  Loading tasks from Azure Table Storage...")
    entities = list(table_client.list_entities())
    tasks = {}
    for entity in entities:
        task_name = entity.get("Task", "")
        if task_name:
            tasks[task_name] = {
                "Due Date": entity.get("DueDate", "TBD"),
                "Status": entity.get("Status", "Not Started"),
                "Priority": entity.get("Priority", "Low"),
                "Category": entity.get("Category", "Admin"),
                "Owner": entity.get("Owner", "Jaymee"),
                "Source": entity.get("Source", "table_storage"),
            }
    print(f"  ✅ Loaded {len(tasks)} tasks from Table Storage")
    return tasks


def load_from_csv(path="data/task_tracker_baseline.csv"):
    """Fetch tasks from CSV"""
    print(f"📊 Loading tasks from {path}...")
    tasks = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)
    print(f"  ✅ Loaded {len(tasks)} tasks from CSV")
    return tasks


# ─────────────────────────────────────────
# MAIN DETECTION LOGIC
# ─────────────────────────────────────────
def run_change_detection():
    print("🕵️  Running AmbitionOS Change Detection Agent...\n")

    conn = get_pg_connection()
    cur = conn.cursor()

    # Load all data sources
    pg_tasks = load_from_postgres()
    table_storage_tasks = load_from_table_storage()
    csv_tasks = load_from_csv()

    # Merge Table Storage into reference (Table Storage takes priority over CSV)
    all_new_tasks = {row["Task"]: row for row in csv_tasks}
    for task_name, data in table_storage_tasks.items():
        all_new_tasks[task_name] = {
            "Task": task_name,
            "Due Date": data["Due Date"],
            "Status": data["Status"],
            "Priority": data["Priority"],
            "Category": data["Category"],
            "Owner": data.get("Owner", "Jaymee"),
            "Source": data.get("Source", "table_storage"),
        }

    changes_log = []
    new_tasks_log = []
    changes_detected = 0
    new_tasks_added = 0

    print("\n🔍 Comparing tasks...\n")

    for task_name, new_task in all_new_tasks.items():

        # ── NEW TASK ──
        if task_name not in pg_tasks:
            print(f"✨ NEW TASK: {task_name}")
            cur.execute("""
                INSERT INTO tasks (task, owner, due_date, status, category, priority, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (task) DO NOTHING
            """, (
                task_name,
                new_task.get("Owner", "Jaymee"),
                new_task.get("Due Date", "TBD"),
                new_task.get("Status", "Not Started"),
                new_task.get("Category", "Admin"),
                new_task.get("Priority", "Low"),
                new_task.get("Source", "change_detection_agent")
            ))
            log_change(cur, task_name, "new_task", "None", new_task.get("Status", "Not Started"))
            sync_to_search(new_task)
            new_tasks_log.append(task_name)
            new_tasks_added += 1
            changes_detected += 1

        # ── EXISTING TASK — CHECK FOR CHANGES ──
        else:
            old = pg_tasks[task_name]
            updated_fields = {}
            fields_to_check = ["Due Date", "Status", "Priority", "Category"]

            for field in fields_to_check:
                old_val = old.get(field, "")
                new_val = new_task.get(field, "")
                if str(old_val).strip() != str(new_val).strip():
                    log_change(cur, task_name, field, old_val, new_val)
                    updated_fields[field] = {"from": old_val, "to": new_val}
                    changes_detected += 1

            if updated_fields:
                print(f"🔄 UPDATED: {task_name}")
                for field, change in updated_fields.items():
                    print(f"   {field}: '{change['from']}' → '{change['to']}'")

                # Update PostgreSQL
                for field, change in updated_fields.items():
                    db_col = field.lower().replace(" ", "_")
                    cur.execute(
                        f"UPDATE tasks SET {db_col} = %s WHERE task = %s",
                        (change["to"], task_name)
                    )

                # Sync to Azure AI Search
                sync_to_search({**new_task, "task": task_name})

                # Trigger Power Automate for high priority changes
                if new_task.get("Priority") == "High" or old.get("Priority") == "High":
                    trigger_power_automate(task_name, updated_fields, new_task.get("Priority", "High"))

                changes_log.append({
                    "task": task_name,
                    "changes": updated_fields,
                    "priority": new_task.get("Priority", "Low")
                })

    conn.commit()
    cur.close()
    conn.close()

    # ── CLAUDE AI SUMMARY ──
    print("\n" + "="*50)
    print("🤖 CLAUDE AI SUMMARY")
    print("="*50)
    summary = get_claude_summary(changes_log, new_tasks_log)
    print(summary)

    # ── FINAL REPORT ──
    print("\n" + "="*50)
    print("✅ Change Detection Complete!")
    print(f"   - {new_tasks_added} new tasks added")
    print(f"   - {len(changes_log)} tasks updated")
    print(f"   - {changes_detected} total changes logged to PostgreSQL")
    print(f"   - Azure AI Search synced ✅")
    print("="*50)


if __name__ == "__main__":
    run_change_detection()