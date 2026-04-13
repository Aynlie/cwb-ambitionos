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
        cur.execute("SELECT definition FROM pg_views WHERE viewname = 'vw_onboarding';")
        row = cur.fetchone()
        if row:
            print(row[0])
        else:
            print("View 'vw_onboarding' not found.")
finally:
    conn.close()
