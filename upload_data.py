import os
import csv
import uuid
from dotenv import load_dotenv
from azure.data.tables import TableServiceClient
from azure.core.exceptions import ResourceExistsError

load_dotenv()

# 1. Connect to Azure Table Storage
conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
table_name = os.getenv("AZURE_TABLE_NAME")

service = TableServiceClient.from_connection_string(conn_str)

# 2. Ensure the table exists
try:
    service.create_table(table_name)
    print(f"Created table: {table_name}")
except ResourceExistsError:
    print(f"Table '{table_name}' already exists.")

table_client = service.get_table_client(table_name)

# 3. Read the CSV and upload each row
csv_file_path = "task_tracker_baseline.csv"

print(f"Uploading data from {csv_file_path}...")

with open(csv_file_path, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    # Strip whitespace from header names just in case
    reader.fieldnames = [name.strip() for name in reader.fieldnames]
    
    count = 0
    for row in reader:
        # Azure Tables require a PartitionKey and a RowKey
        # Let's use the 'Category' as PartitionKey, and a unique UUID as RowKey
        category = row.get("Category", "General").strip()
        category = category if category else "General"
        
        entity = {
            "PartitionKey": category,
            "RowKey": str(uuid.uuid4()),
            "Task": row.get("Task", "").strip(),
            "DueDate": row.get("Due Date", "").strip(),
            "Status": row.get("Status", "").strip(),
            "Priority": row.get("Priority", "").strip()
        }
        
        # Insert entity into the table
        table_client.create_entity(entity=entity)
        print(f"Uploaded: {entity['Task']} ({entity['PartitionKey']})")
        count += 1

print(f"Successfully uploaded {count} tasks to Azure Table Storage!")
