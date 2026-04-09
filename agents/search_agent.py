import os
import csv
import time
from dotenv import load_dotenv
import base64
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
)
from azure.data.tables import TableServiceClient

load_dotenv()

# Azure AI Search config
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")

# Clients
search_credential = AzureKeyCredential(SEARCH_KEY)
index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=search_credential)
search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=SEARCH_INDEX, credential=search_credential)

# Azure Table Storage client
table_service = TableServiceClient.from_connection_string(
    os.getenv("AZURE_STORAGE_CONNECTION_STRING")
)
table_client = table_service.get_table_client("ambitionosdata")


# ─────────────────────────────────────────
# STEP 0 — Utility: Safe ID Generation
# ─────────────────────────────────────────
def generate_safe_id(task_name: str, owner: str = "Jaymee") -> str:
    """
    Generate a valid Azure Search document ID.
    Must be alphanumeric, underscores, or dashes. 
    Unified with change_detection_agent.py: base64(task_name_owner)
    """
    if not task_name:
        return "unknown_task"
    combined = f"{task_name}_{owner}".strip().lower()
    return base64.urlsafe_b64encode(combined.encode('utf-8')).decode('utf-8').rstrip('=')

# ─────────────────────────────────────────
# STEP 1 — Create or update the search index
# ─────────────────────────────────────────
def create_index():
    """Create Azure AI Search index with task schema (Purges old index if exists)"""
    print("📐 Setting up Azure AI Search index...")

    try:
        index_client.delete_index(SEARCH_INDEX)
        print(f"  🗑️  Old index '{SEARCH_INDEX}' purged.")
    except Exception:
        pass

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="task", type=SearchFieldDataType.String),
        SimpleField(name="owner", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="due_date", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="status", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="priority", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
    ]

    index = SearchIndex(name=SEARCH_INDEX, fields=fields)
    index_client.create_or_update_index(index)
    print(f"  ✅ Index '{SEARCH_INDEX}' ready!")


# ─────────────────────────────────────────
# STEP 2 — Index tasks from Table Storage
# ─────────────────────────────────────────
def index_from_table_storage():
    """Pull tasks from Azure Table Storage and push to Search index"""
    print("\n☁️  Indexing tasks from Azure Table Storage...")

    entities = list(table_client.list_entities())
    documents = []

    for entity in entities:
        task_name = entity.get("Task", "")
        owner = entity.get("Owner", "Jaymee")
        doc = {
            "id": generate_safe_id(task_name, owner),
            "task": task_name,
            "owner": entity.get("Owner", "Jaymee"),
            "due_date": entity.get("DueDate", "TBD"),
            "status": entity.get("Status", "Not Started"),
            "category": entity.get("Category", "Admin"),
            "priority": entity.get("Priority", "Low"),
            "source": entity.get("Source", "table_storage"),
        }
        documents.append(doc)

    if documents:
        results = search_client.upload_documents(documents)
        succeeded = sum(1 for r in results if r.succeeded)
        print(f"  ✅ Indexed {succeeded}/{len(documents)} tasks from Table Storage!")
    else:
        print("  ⚠️  No tasks found in Table Storage.")


# ─────────────────────────────────────────
# STEP 3 — Index tasks from CSV
# ─────────────────────────────────────────
def index_from_csv(csv_path="data/powerbi_export.csv"):
    """Pull tasks from CSV and push to Search index"""
    print(f"\n📊 Indexing tasks from {csv_path}...")

    documents = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_name = row.get("Task", "")
            owner = row.get("Owner", "Jaymee")
            doc = {
                "id": generate_safe_id(task_name, owner),
                "task": task_name,
                "owner": row.get("Owner", "Jaymee"),
                "due_date": row.get("DueDate", row.get("Due Date", "TBD")),
                "status": row.get("Status", "Not Started"),
                "category": row.get("Category", "Admin"),
                "priority": row.get("Priority", "Low"),
                "source": row.get("Source", csv_path),
            }
            documents.append(doc)

    if documents:
        results = search_client.upload_documents(documents)
        succeeded = sum(1 for r in results if r.succeeded)
        print(f"  ✅ Indexed {succeeded}/{len(documents)} tasks from CSV!")
    else:
        print("  ⚠️  No tasks found in CSV.")


# ─────────────────────────────────────────
# STEP 4 — Search tasks
# ─────────────────────────────────────────
def search_tasks(query="*", filter=None, top=10):
    """Search tasks by keyword, with optional filter"""
    print(f"\n🔍 Searching for: '{query}'" + (f" | Filter: {filter}" if filter else ""))

    results = search_client.search(
        search_text=query,
        filter=filter,
        top=top,
        include_total_count=True
    )

    hits = list(results)
    print(f"  📋 Found {len(hits)} result(s):\n")

    for r in hits:
        print(f"  [{r['priority']}] {r['task']}")
        print(f"         Status: {r['status']} | Category: {r['category']} | Due: {r['due_date']}")
        print()

    return hits


# ─────────────────────────────────────────
# STEP 5 — Index a single task (hook for extraction_agent.py)
# ─────────────────────────────────────────
def index_single_task(task: dict):
    """
    Index one task directly — call this from extraction_agent.py
    after save_task() to keep Search in sync.

    Usage in extraction_agent.py:
        from agents.search_agent import index_single_task
        index_single_task(task)
    """
    task_name = task.get("task", "")
    owner = task.get("owner", "Jaymee")
    doc = {
        "id": generate_safe_id(task_name, owner),
        "task": task_name,
        "owner": task.get("owner", "Jaymee"),
        "due_date": task.get("due_date", "TBD"),
        "status": task.get("status", "Not Started"),
        "category": task.get("category", "Admin"),
        "priority": task.get("priority", "Low"),
        "source": task.get("source", "extraction_agent"),
    }
    
    try:
        results = search_client.upload_documents([doc])
        if results and results[0].succeeded:
            print(f"  🔍 Indexed in Search: {task_name}")
        else:
            print(f"  ⚠️  Failed to index: {task_name} (Succeeded: False)")
    except Exception as e:
        print(f"  ❌ Search indexing error for '{task_name}': {e}")


# ─────────────────────────────────────────
# MAIN — Run full indexing pipeline
# ─────────────────────────────────────────
def run():
    print("🤖 AmbitionOS Search Agent Starting...\n")

    # 1. Create index schema
    create_index()

    # 2. Index all data sources
    index_from_table_storage()
    index_from_csv("data/powerbi_export.csv")

    # 3. Demo searches
    print("\n" + "="*50)
    print("🔎 DEMO SEARCHES (Waiting 3s for propagation...)")
    print("="*50)
    time.sleep(3)

    # Search all tasks
    search_tasks("*")

    # Search high priority only
    search_tasks("*", filter="priority eq 'High'")

    # Search by keyword
    search_tasks("ISACA")

    # Search by category
    search_tasks("*", filter="category eq 'Certification'")

    print("🎉 Search Agent done!")


if __name__ == "__main__":
    run()