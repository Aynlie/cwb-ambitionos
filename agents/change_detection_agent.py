import os
import csv
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_pg_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", 5432),
        sslmode="require"
    )

def log_change(cur, task_name, field_changed, old_value, new_value):
    """Insert a record into the change_logs table"""
    cur.execute("""
        INSERT INTO change_logs (task_name, field_changed, old_value, new_value)
        VALUES (%s, %s, %s, %s)
    """, (task_name, field_changed, str(old_value), str(new_value)))

def run_change_detection():
    print("🕵️  Running AmbitionOS Change Detection Agent...\n")
    
    conn = get_pg_connection()
    cur = conn.cursor()
    
    # 1. Fetch current (old) tasks from PostgreSQL
    cur.execute("SELECT task, due_date, status, priority, category FROM tasks")
    old_tasks = {}
    for row in cur.fetchall():
        task_name, due_date, status, priority, category = row
        old_tasks[task_name] = {
            "Due Date": due_date,
            "Status": status,
            "Priority": priority,
            "Category": category
        }
    
    # 2. Read new tasks from CSV
    new_tasks = []
    with open("data/task_tracker_baseline.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            new_tasks.append(row)
            
    changes_detected = 0
    new_tasks_added = 0
    
    # 3. Compare and detect changes
    for new_task in new_tasks:
        task_name = new_task["Task"]
        
        # New task check
        if task_name not in old_tasks:
            print(f"✨ NEW TASK DETECTED: {task_name}")
            
            # Insert new task into Postgres
            cur.execute("""
                INSERT INTO tasks (task, owner, due_date, status, category, priority, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                task_name, "Jaymee", new_task["Due Date"], new_task["Status"],
                new_task["Category"], new_task["Priority"], "task_tracker_baseline.csv"
            ))
            
            # Log the addition
            log_change(cur, task_name, "new_task", "None", new_task["Status"])
            new_tasks_added += 1
            changes_detected += 1
            
        else:
            # Check for modifications
            old = old_tasks[task_name]
            updated_fields = {}
            fields_to_check = ["Due Date", "Status", "Priority", "Category"]
            
            for field in fields_to_check:
                if old[field] != new_task[field]:
                    log_change(cur, task_name, field, old[field], new_task[field])
                    updated_fields[field] = new_task[field]
                    changes_detected += 1
                    
            if updated_fields:
                print(f"🔄 UPDATED {task_name}: {updated_fields}")
                # Build the dynamic UPDATE query
                for field, new_val in updated_fields.items():
                    # Map the CSV field name to DB column name
                    db_col = field.lower().replace(" ", "_")
                    cur.execute(f"UPDATE tasks SET {db_col} = %s WHERE task = %s", (new_val, task_name))

    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\n✅ Change Detection Complete!")
    print(f"   - {new_tasks_added} new tasks added")
    print(f"   - {changes_detected} total changes logged to PostgreSQL")

if __name__ == "__main__":
    run_change_detection()
