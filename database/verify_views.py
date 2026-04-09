import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def verify_views():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", 5432),
        sslmode="require"
    )
    cur = conn.cursor()

    print("=" * 60)
    print("SQL VIEW VERIFICATION REPORT")
    print("=" * 60)

    # --- vw_gantt ---
    cur.execute("SELECT COUNT(*) FROM vw_gantt")
    count = cur.fetchone()[0]
    print(f"\n[vw_gantt] {count} rows")
    if count > 0:
        cur.execute("SELECT task, priority, due_date, priority_order FROM vw_gantt LIMIT 3")
        for row in cur.fetchall():
            print(f"  {row}")

    # --- vw_change_log ---
    cur.execute("SELECT COUNT(*) FROM vw_change_log")
    count = cur.fetchone()[0]
    print(f"\n[vw_change_log] {count} rows")
    if count > 0:
        cur.execute("SELECT detected_at, task_name, changed_field, old_value, new_value FROM vw_change_log LIMIT 3")
        for row in cur.fetchall():
            print(f"  {row}")

    # --- vw_onboarding ---
    cur.execute("SELECT COUNT(*) FROM vw_onboarding")
    count = cur.fetchone()[0]
    print(f"\n[vw_onboarding] {count} rows")
    if count > 0:
        cur.execute("SELECT task, source, approval_status, confidence FROM vw_onboarding LIMIT 3")
        for row in cur.fetchall():
            print(f"  {row}")

    # --- vw_overview ---
    cur.execute("SELECT COUNT(*) FROM vw_overview")
    count = cur.fetchone()[0]
    print(f"\n[vw_overview] {count} rows")
    if count > 0:
        cur.execute("SELECT task, urgency_band, status, confidence FROM vw_overview LIMIT 3")
        for row in cur.fetchall():
            print(f"  {row}")

    # --- Summary stats for Power BI cards ---
    print("\n" + "=" * 60)
    print("POWER BI CARD VALUES (from vw_overview)")
    print("=" * 60)
    cur.execute("SELECT COUNT(*) FROM vw_overview")
    print(f"  Total Approved Tasks: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM vw_overview WHERE priority = 'High'")
    print(f"  High Priority Tasks:  {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM tasks WHERE approval_status = 'Pending'")
    print(f"  Pending Approvals:    {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(DISTINCT urgency_band) FROM vw_overview")
    print(f"  Urgency Bands:        {cur.fetchone()[0]}")
    cur.execute("SELECT urgency_band, COUNT(*) FROM vw_overview GROUP BY urgency_band")
    for row in cur.fetchall():
        print(f"    {row[0]}: {row[1]}")

    print("\n" + "=" * 60)
    print("ALL VIEWS VERIFIED SUCCESSFULLY")
    print("=" * 60)

    cur.close()
    conn.close()

if __name__ == "__main__":
    verify_views()
