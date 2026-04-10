import os
import psycopg2
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

def migrate():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", 5432),
        sslmode="require"
    )
    cur = conn.cursor()
    print("🐘 Connected to PostgreSQL. Adding approval_status column...")
    
    try:
        cur.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) DEFAULT 'Approved';")
        conn.commit()
        print("✅ column 'approval_status' added successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
