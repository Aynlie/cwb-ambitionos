import os
import sys
import json
import anthropic
from dotenv import load_dotenv
from agents.extraction_agent import save_task
from database.sync_tasks import sync_to_postgres

# ─────────────────────────────────────────
# CONFIG & ENCODING
# ─────────────────────────────────────────
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

# Set to False once Anthropic credits are topped up
MOCK_MODE = True 

# Claude Config
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

EXTRACTION_PROMPT = """
You are an AI assistant that extracts structured tasks from student
emails and syllabi. Return ONLY a valid JSON array, no explanation.

Each task object must have these exact fields:
- task: string
- owner: string (default "Admin" if not mentioned)
- due_date: string (YYYY-MM-DD format, or "This week" if unclear)
- status: string (one of: Not Started, In Progress, Completed, Blocked)
- category: string (one of: Scholarship, Certification, School,
  Internship, Ambassador, Course, Learning, Content, Personal, Admin)
- priority: string (one of: High, Medium, Low)
- source: string (one of: Email, Syllabus, Meeting Notes)
- confidence: string (one of: High, Medium, Low)

Low confidence = due date unclear, owner missing, or task is ambiguous.

Text to extract from:
{input_text}
"""

# ─────────────────────────────────────────
# CLAUDE EXTRACTION LOGIC
# ─────────────────────────────────────────
def extract_tasks_with_claude(input_text):
    """Uses Claude to extract structured JSON tasks from text"""
    
    if MOCK_MODE:
        print("🧪 MOCK_MODE: Generating simulated tasks for onboarding...")
        return [
            {
                "task": "Welcome to AmbitionOS!",
                "owner": "Admin",
                "due_date": "2026-04-09",
                "status": "Not Started",
                "category": "Admin",
                "priority": "High",
                "source": "Meeting Notes",
                "confidence": "High"
            },
            {
                "task": "Complete MLSA Profile Sync",
                "owner": "Jaymee",
                "due_date": "This week",
                "status": "In Progress",
                "category": "Ambassador",
                "priority": "Medium",
                "source": "Email",
                "confidence": "Medium"
            }
        ]

    print(f"🤖 Calling Claude ({CLAUDE_MODEL}) to parse onboarding items...")
    
    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(input_text=input_text)}]
        )
        
        raw_content = response.content[0].text
        # Clean up possible markdown code blocks
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0].strip()
        
        return json.loads(raw_content)

    except Exception as e:
        print(f"  ❌ Claude Error: {e}")
        return []

# ─────────────────────────────────────────
# ONBOARDING PIPELINE
# ─────────────────────────────────────────
def run_onboarding(file_path):
    """Main function to onboard tasks from a file"""
    print(f"🚀 Starting Onboarding Agent for: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"  ❌ Error: File not found at {file_path}")
        return

    # 1. Read input
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 2. Extract with Claude (or Mock)
    tasks = extract_tasks_with_claude(content)
    
    if not tasks:
        print("  ⚠️ No tasks extracted.")
        return

    print(f"  ✨ Extracted {len(tasks)} tasks. Processing...")
    
    # 3. Save to Table Storage & Index to Search
    source_name = os.path.basename(file_path)
    for task in tasks:
        # save_task handles Table Storage + Search Indexing
        save_task(task, source_name)
    
    # 4. Sync to PostgreSQL
    print("\n🐘 Syncing new tasks to PostgreSQL...")
    sync_to_postgres(tasks)
    
    print("\n🎉 Onboarding complete! Check your dashboard.")

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    # Test with email threads
    test_file = "data/email_threads.txt"
    run_onboarding(test_file)
