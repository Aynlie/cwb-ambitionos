import sys
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
        # Create a safe cast function so things like "Today" or "This week" don't crash the view
        cur.execute("""
        CREATE OR REPLACE FUNCTION try_cast_date(p_in text)
        RETURNS date AS $$
        BEGIN
            RETURN p_in::date;
        EXCEPTION WHEN others THEN
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """)

        cur.execute("DROP VIEW IF EXISTS public.vw_overview;")

        cur.execute("""
        CREATE VIEW public.vw_overview AS
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
        dependency,
        CASE
            WHEN try_cast_date(due_date) <= CURRENT_DATE + INTERVAL '3 days' THEN 'Critical'
            WHEN try_cast_date(due_date) <= CURRENT_DATE + INTERVAL '7 days' THEN 'High'
            ELSE 'Normal'
        END AS urgency_band
        FROM public.tasks
        WHERE approval_status = 'Approved';
        """)
    conn.commit()
    print("Successfully updated vw_overview")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
