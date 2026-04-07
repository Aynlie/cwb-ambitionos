import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

load_dotenv()

conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
client = BlobServiceClient.from_connection_string(conn_str)

# Create container
container_name = "ambitionos-data"
try:
    client.create_container(container_name)
    print(f"✅ Container '{container_name}' created!")
except Exception:
    print(f"ℹ️ Container already exists")

# Upload files
files = [
    "data/meeting_notes.txt",
    "data/email_threads.txt",
    "data/task_tracker_baseline.csv"
]

for file_path in files:
    with open(file_path, "rb") as f:
        blob_name = os.path.basename(file_path)
        client.get_blob_client(container=container_name, blob=blob_name).upload_blob(f, overwrite=True)
        print(f"✅ Uploaded: {blob_name}")
