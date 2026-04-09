import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", 5432),
        sslmode="require"
    )

def setup_database():
    """Create tables if they don't exist"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Tasks table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            task VARCHAR(255) NOT NULL,
            owner VARCHAR(100),
            due_date VARCHAR(100),
            status VARCHAR(50),
            category VARCHAR(100),
            priority VARCHAR(50),
            source VARCHAR(100),
            confidence VARCHAR(20) DEFAULT 'Medium',
            approval_status VARCHAR(20) DEFAULT 'Approved',
            extracted_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # Change logs table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS change_logs (
            id SERIAL PRIMARY KEY,
            task_name VARCHAR(255),
            field_changed VARCHAR(100),
            old_value VARCHAR(255),
            new_value VARCHAR(255),
            changed_at TIMESTAMP DEFAULT NOW()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database tables created successfully!")

def sync_tasks_from_table_storage(tasks):
    """Sync tasks from Azure Table Storage to PostgreSQL"""
    conn = get_connection()
    cur = conn.cursor()
    
    for task in tasks:
        cur.execute("""
            INSERT INTO tasks 
                (task, owner, due_date, status, category, priority, source, confidence, approval_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """, (
            task.get("task", ""),
            task.get("owner", "Jaymee"),
            task.get("due_date", "TBD"),
            task.get("status", "Not Started"),
            task.get("category", "General"),
            task.get("priority", "Medium"),
            task.get("source", "manual"),
            task.get("confidence", "Medium"),
            task.get("approval_status", "Approved")
        ))
        print(f"  ✅ Synced: {task.get('task')}")
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"\n✅ {len(tasks)} tasks synced to PostgreSQL!")

if __name__ == "__main__":
    print("🗄️ Setting up AmbitionOS Database...\n")
    setup_database()
