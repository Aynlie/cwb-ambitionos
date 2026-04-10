import os
import sys
import json
import psycopg2
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# ─────────────────────────────────────────
# TAB CONFIG — persona → tabs + categories
# ─────────────────────────────────────────
TAB_CONFIG = {
    "student": {
        "tabs": ["Overview", "My Tasks", "Opportunities", "Research", "Coffee Chat"],
        "categories": ["School", "Admin", "Scholarship", "Internship", "Personal"]
    },
    "professional": {
        "tabs": ["Overview", "Active Tasks", "Change Log", "Gantt", "Pending Approval"],
        "categories": ["Project", "Milestone", "Blocker", "Review", "Completed"]
    },
    "career_shifter": {
        "tabs": ["Overview", "My Goals", "Opportunities", "Upskilling", "Coffee Chat"],
        "categories": ["Learning", "Certification", "Job Hunt", "Networking", "Personal"]
    }
}


# ─────────────────────────────────────────
# DB CONNECTION
# ─────────────────────────────────────────
def get_pg_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", 5432),
        sslmode="require"
    )


# ─────────────────────────────────────────
# SETUP — create user_profiles table
# ─────────────────────────────────────────
def setup_user_profiles_table():
    """Create the user_profiles table if it does not exist"""
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id          SERIAL PRIMARY KEY,
            created_at  TIMESTAMP DEFAULT NOW(),
            name        VARCHAR(100),
            user_type   VARCHAR(50),
            field       VARCHAR(100),
            focus       VARCHAR(100),
            needs       TEXT[],
            tab_config  JSONB,
            onboarded   BOOLEAN DEFAULT FALSE
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("[OK] user_profiles table ready.")


# ─────────────────────────────────────────
# SAVE — insert a new user profile
# ─────────────────────────────────────────
def save_profile(data: dict) -> dict:
    """
    Save a completed onboarding profile to PostgreSQL.
    Resolves tab_config from user_type automatically.
    Returns the saved tab_config dict.
    """
    user_type = data.get("user_type", "student").lower().replace(" ", "_")
    tab_config = TAB_CONFIG.get(user_type, TAB_CONFIG["student"])

    conn = get_pg_connection()
    cur = conn.cursor()

    # Clear any previous profiles (single-user demo model)
    cur.execute("DELETE FROM user_profiles;")

    cur.execute("""
        INSERT INTO user_profiles (name, user_type, field, focus, needs, tab_config, onboarded)
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
    """, (
        data.get("name", "User"),
        user_type,
        data.get("field"),
        data.get("focus"),
        data.get("needs", []),
        json.dumps(tab_config)
    ))

    conn.commit()
    cur.close()
    conn.close()

    print(f"[OK] Profile saved for {data.get('name')} as {user_type}.")
    return tab_config


# ─────────────────────────────────────────
# GET — fetch current profile
# ─────────────────────────────────────────
def get_profile() -> dict | None:
    """
    Returns the current user profile dict, or None if no profile exists.
    Always returns LIMIT 1 (single-user demo model).
    """
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, user_type, field, focus, needs, tab_config, onboarded
            FROM user_profiles
            WHERE onboarded = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row is None:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "user_type": row[2],
            "field": row[3],
            "focus": row[4],
            "needs": row[5],
            "tab_config": row[6],   # already a dict from JSONB
            "onboarded": row[7]
        }
    except Exception as e:
        print(f"[WARN] Could not fetch profile: {e}")
        return None


# ─────────────────────────────────────────
# MAIN — run directly to set up table
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("[RUN] Setting up user_profiles table...")
    setup_user_profiles_table()
    print("[DONE] Database ready for Amby onboarding.")
