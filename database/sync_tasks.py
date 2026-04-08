import os
from dotenv import load_dotenv
from azure.data.tables import TableServiceClient
import psycopg2

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

def get_tasks_from_table_storage():
    """Fetch all tasks from Azure Table Storage"""
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    table_service = TableServiceClient.from_connection_string(conn_str)
    table_client = table_service.get_table_client("ambitionosdata")
    
    tasks = []
    for entity in table_client.list_entities():
        tasks.append({
            "task": entity.get("Task", ""),
            "owner": entity.get("Owner", "Jaymee"),
            "due_date": entity.get("DueDate", "TBD"),
            "status": entity.get("Status", "Not Started"),
            "category": entity.get("Category", "General"),
            "priority": entity.get("Priority", "Medium"),
            "source": entity.get("Source", "manual")
        })
    return tasks

def sync_to_postgres(tasks):
    """Sync tasks to PostgreSQL"""
    conn = get_pg_connection()
    cur = conn.cursor()
    
    synced = 0
    for task in tasks:
        cur.execute("""
            INSERT INTO tasks 
                (task, owner, due_date, status, category, priority, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """, (
            task["task"],
            task["owner"],
            task["due_date"],
            task["status"],
            task["category"],
            task["priority"],
            task["source"]
        ))
        print(f"  ✅ Synced: {task['task']}")
        synced += 1
    
    conn.commit()
    cur.close()
    conn.close()
    return synced

def run():
    print("🔄 Syncing tasks from Azure Table Storage → PostgreSQL...\n")
    tasks = get_tasks_from_table_storage()
    print(f"📋 Found {len(tasks)} tasks in Table Storage\n")
    count = sync_to_postgres(tasks)
    print(f"\n✅ {count} tasks synced to PostgreSQL!")

if __name__ == "__main__":
    run()
