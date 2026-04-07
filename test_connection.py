import os
from dotenv import load_dotenv
from azure.data.tables import TableServiceClient

load_dotenv()

conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
table_name = os.getenv("AZURE_TABLE_NAME")

service = TableServiceClient.from_connection_string(conn_str)
table = service.get_table_client(table_name)

print("Connected to Azure Table Storage!")
print(f"Table: {table_name}")
