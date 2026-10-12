
import os
import json
from google.oauth2 import service_account
from google.cloud import bigquery

# Verify credentials
key_path = "floatchat-key.json"
credentials = service_account.Credentials.from_service_account_file(key_path)
project_id = credentials.project_id
print(f"Project ID: {project_id}")

client = bigquery.Client(credentials=credentials, project=project_id)
dataset_id = "argo"
table_id = "argo_profiles"

table_ref = f"{project_id}.{dataset_id}.{table_id}"
print(f"Inspecting table: {table_ref}")

try:
    table = client.get_table(table_ref)
    print("\nTable Schema:")
    for schema_field in table.schema:
        print(f" - {schema_field.name} ({schema_field.field_type})")
except Exception as e:
    print(f"Error getting table: {e}")
