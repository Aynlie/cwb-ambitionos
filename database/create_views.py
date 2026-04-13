# database/create_views.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def create_views():
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            port=os.getenv("POSTGRES_PORT", 5432),
            sslmode="require"
        )
        cur = conn.cursor()

        # 1. Gantt Chart View
        # Note: Added cast for due_date as it is stored as VARCHAR
        GANTT_SQL = """
        CREATE OR REPLACE VIEW vw_gantt AS
        SELECT
            task,
            owner,
            due_date,
            status,
            priority,
            category,
            confidence,
            approval_status,
            CASE priority
                WHEN 'High'   THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'Low'    THEN 3
                ELSE 4
            END AS priority_order
        FROM tasks
        WHERE status != 'Completed'
        AND approval_status = 'Approved'
        AND due_date IS NOT NULL
        ORDER BY priority_order, due_date;
        """

        # 2. Change Log Timeline View
        # Corrected to match actual 'change_logs' table schema
        CHANGE_LOG_SQL = """
        CREATE OR REPLACE VIEW vw_change_log AS
        SELECT
            id,
            changed_at AS detected_at,
            task_name,
            field_changed AS changed_field,
            old_value,
            new_value
        FROM change_logs
        ORDER BY changed_at DESC;
        """

        # 3. Onboarding Tasks View
        ONBOARDING_SQL = """
        CREATE OR REPLACE VIEW vw_onboarding AS
        SELECT
            task,
            owner,
            due_date,
            status,
            category,
            priority,
            confidence,
            approval_status,
            source
        FROM tasks
        WHERE source IN (
          'Email', 'Syllabus', 'Meeting Notes',
          'email_threads.txt', 'meeting_notes.txt',
          'task_tracker_baseline.csv', 'csv_baseline'
        )
        ORDER BY approval_status DESC, priority;
        """

        # 4. Dashboard Overview View
        # Note: Handling VARCHAR to DATE conversion for urgency bands
        OVERVIEW_SQL = """
        CREATE OR REPLACE VIEW vw_overview AS
        SELECT
            task,
            owner,
            due_date,
            status,
            category,
            priority,
            source,
            confidence,
            approval_status,
            CASE
                WHEN due_date ~ '^\\d{4}-\\d{2}-\\d{2}$' AND CAST(due_date AS DATE) <= CURRENT_DATE + INTERVAL '7 days'
                THEN 'Due This Week'
                WHEN due_date ~ '^\\d{4}-\\d{2}-\\d{2}$' AND CAST(due_date AS DATE) <= CURRENT_DATE + INTERVAL '30 days'
                THEN 'Due This Month'
                ELSE 'Upcoming'
            END AS urgency_band
        FROM tasks
        WHERE approval_status = 'Approved'
        ORDER BY due_date;
        """

        views = [
            ("vw_gantt",       GANTT_SQL),
            ("vw_change_log",  CHANGE_LOG_SQL),
            ("vw_onboarding",  ONBOARDING_SQL),
            ("vw_overview",    OVERVIEW_SQL),
        ]

        for name, sql in views:
            cur.execute(sql)
            print(f"Created view: {name}")

        conn.commit()
        cur.close()
        conn.close()
        print("All views created successfully!")
        
    except Exception as e:
        print(f"Error creating views: {e}")

if __name__ == "__main__":
    create_views()
