import os
import csv
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.data.tables import TableServiceClient
from datetime import datetime
from agents.search_agent import index_single_task

load_dotenv()

# Azure AI Language client
language_client = TextAnalyticsClient(
    endpoint=os.getenv("AZURE_LANGUAGE_ENDPOINT"),
    credential=AzureKeyCredential(os.getenv("AZURE_LANGUAGE_KEY"))
)

# Azure Table Storage client
table_service = TableServiceClient.from_connection_string(
    os.getenv("AZURE_STORAGE_CONNECTION_STRING")
)
table_client = table_service.get_table_client("ambitionosdata")

def extract_from_text(text):
    """Extract key phrases and entities from text"""
    print("🧠 Extracting key phrases...")
    key_phrases = language_client.extract_key_phrases([text])[0]
    
    print("🔍 Recognizing entities...")
    entities = language_client.recognize_entities([text])[0]
    
    tasks = []
    for phrase in key_phrases.key_phrases:
        # Look for action-oriented phrases
        action_words = ["apply", "complete", "submit", "request", 
                       "post", "start", "finish", "review", "update"]
        if any(word in phrase.lower() for word in action_words):
            # Try to find associated date
            due_date = "TBD"
            owner = "Jaymee"
            
            for entity in entities.entities:
                if entity.category == "DateTime":
                    due_date = entity.text
                if entity.category == "Person":
                    owner = entity.text
            
            tasks.append({
                "task": phrase,
                "owner": owner,
                "due_date": due_date,
                "status": "Not Started",
                "category": categorize_task(phrase),
                "priority": prioritize_task(phrase)
            })
    
    return tasks

def categorize_task(task_text):
    """Auto-categorize based on keywords"""
    task_lower = task_text.lower()
    if any(w in task_lower for w in ["scholarship", "isaca", "buildher"]):
        return "Scholarship"
    elif any(w in task_lower for w in ["internship", "globe", "dict", "dost"]):
        return "Internship"
    elif any(w in task_lower for w in ["ambassador", "mlsa", "github", "samsung"]):
        return "Ambassador"
    elif any(w in task_lower for w in ["cisco", "cert", "course"]):
        return "Certification"
    elif any(w in task_lower for w in ["instagram", "post", "content"]):
        return "Content"
    else:
        return "Admin"

def prioritize_task(task_text):
    """Auto-prioritize based on keywords"""
    task_lower = task_text.lower()
    if any(w in task_lower for w in ["today", "urgent", "deadline", "asap"]):
        return "High"
    elif any(w in task_lower for w in ["this week", "soon"]):
        return "Medium"
    else:
        return "Low"

def save_task(task, source):
    """Save task to Azure Table Storage"""
    entity = {
        "PartitionKey": "tasks",
        "RowKey": task["task"].replace(" ", "_")[:50],
        "Task": task["task"],
        "Owner": task["owner"],
        "DueDate": task["due_date"],
        "Status": task["status"],
        "Category": task["category"],
        "Priority": task["priority"],
        "Source": source,
        "ExtractedAt": datetime.utcnow().isoformat()
    }
    table_client.upsert_entity(entity)
    print(f"  ✅ Saved: {task['task']}")
    
    # Push to Search Index
    task_with_source = task.copy()
    task_with_source["source"] = source
    try:
        index_single_task(task_with_source)
    except Exception as e:
        print(f"  ⚠️ Error indexing task in search: {e}")

def load_from_csv():
    """Load tasks directly from CSV file"""
    print("📊 Loading tasks from CSV...")
    
    with open("data/task_tracker_baseline.csv", "r") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            entity = {
                "PartitionKey": "tasks",
                "RowKey": row["Task"].replace(" ", "_")[:50],
                "Task": row["Task"],
                "Owner": "Jaymee",
                "DueDate": row["Due Date"],
                "Status": row["Status"],
                "Category": row["Category"],
                "Priority": row["Priority"],
                "Source": "task_tracker_baseline.csv",
                "ExtractedAt": datetime.utcnow().isoformat()
            }
            table_client.upsert_entity(entity)
            print(f"  ✅ Saved: {row['Task']}")
            count += 1
    
    print(f"\n✅ Loaded {count} tasks from CSV!")
    return count

def run():
    print("🤖 AmbitionOS Extraction Agent Starting...\n")
    
    # Step 1 — Load structured data from CSV
    load_from_csv()
    
    # Step 2 — Extract additional tasks from meeting notes
    print("\n📄 Reading meeting_notes.txt...")
    with open("data/meeting_notes.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    tasks = extract_from_text(text)
    print(f"\n📋 Found {len(tasks)} additional tasks from notes\n")
    for task in tasks:
        save_task(task, "meeting_notes.txt")
    
    print("\n🎉 All done!")

if __name__ == "__main__":
    run()
