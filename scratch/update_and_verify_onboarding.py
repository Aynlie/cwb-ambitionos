import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    database=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    port=os.getenv("POSTGRES_PORT", 5432),
    sslmode="require"
)
try:
    with conn.cursor() as cur:
        # Update the view
        cur.execute("""
        CREATE OR REPLACE VIEW public.vw_onboarding AS
        SELECT task, owner, due_date, status, category, priority,
               confidence, approval_status, source
        FROM tasks
        WHERE source IN (
          'Email', 'Syllabus', 'Meeting Notes',
          'email_threads.txt', 'meeting_notes.txt',
          'task_tracker_baseline.csv', 'csv_baseline'
        )
        ORDER BY approval_status DESC, priority;
        """)
        conn.commit()
        print("View updated successfully.")

        # Verify counts
        cur.execute("SELECT source, COUNT(*) FROM public.vw_onboarding GROUP BY source;")
        results = cur.fetchall()
        for row in results:
            print(f"{row[0]}: {row[1]}")
finally:
    conn.close()
