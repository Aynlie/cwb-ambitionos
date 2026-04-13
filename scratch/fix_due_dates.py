import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL Connection
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    database=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    port=os.getenv("POSTGRES_PORT", 5432),
    sslmode="require"
)

updates = [
    ("2026-04-20", "Cisco Intro to Cybersecurity"),
    ("2026-07-01", "GitHub Campus Experts"),
    ("2026-05-01", "Samsung Galaxy Campus B4"),
    ("2026-05-05", "ISACA SheLeadsTech"),
    ("2027-01-01", "Globe Summer Internship"),
    ("2027-01-01", "Start"),
    ("2027-01-01", "Request"),
    ("2026-04-18", "Start Cisco Intro"),
    ("2026-04-18", "Forage ANZ"),
    ("2026-04-18", "Test Debug Task"),
    ("2026-04-18", "Complete MLSA Profile Sync"),
    ("2026-04-18", "Apply MLSA"),
    ("2026-04-18", "Request HAU transcript"),
    ("2026-04-13", "Post Instagram carousel")
]

try:
    with conn.cursor() as cur:
        for due_date, task in updates:
            cur.execute("UPDATE tasks SET due_date = %s WHERE task = %s", (due_date, task))
        conn.commit()
        print("Successfully updated task due dates.")

        # Verification
        print("\nVerifying updated due dates:")
        cur.execute("SELECT task, due_date FROM tasks ORDER BY due_date;")
        for row in cur.fetchall():
            print(row)
finally:
    conn.close()
