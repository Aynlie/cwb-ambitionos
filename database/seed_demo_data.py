# database/seed_demo_data.py
import os
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import random

load_dotenv()

def seed_demo_data():
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

        print("Seeding historical change logs for Power BI demo...")

        # Get some real tasks to attach logs to
        cur.execute("SELECT task FROM tasks LIMIT 5")
        tasks = [row[0] for row in cur.fetchall()]

        fields = ["status", "priority", "due_date"]
        statuses = ["Not Started", "In Progress", "Blocked", "Completed"]
        priorities = ["Low", "Medium", "High"]

        # Generate 20 random changes over the last 7 days
        for i in range(20):
            task = random.choice(tasks)
            field = random.choice(fields)
            
            if field == "status":
                old, new = random.sample(statuses, 2)
            elif field == "priority":
                old, new = random.sample(priorities, 2)
            else:
                old = (datetime.now() + timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d")
                new = (datetime.now() + timedelta(days=random.randint(11, 20))).strftime("%Y-%m-%d")

            # Randomized timestamp within the last week
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            changed_at = datetime.now() - timedelta(days=days_ago, hours=hours_ago)

            cur.execute("""
                INSERT INTO change_logs (task_name, field_changed, old_value, new_value, changed_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (task, field, old, new, changed_at))

        conn.commit()
        print(f"Successfully seeded {20} historical change logs!")

        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error seeding data: {e}")

if __name__ == "__main__":
    seed_demo_data()
