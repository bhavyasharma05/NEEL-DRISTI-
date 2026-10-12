
import os
import json
from google.oauth2 import service_account
from google.cloud import bigquery

# Verify credentials
key_path = "floatchat-key.json"
if not os.path.exists(key_path):
    print(f"Key file not found: {key_path}")
    exit(1)

print(f"Using key file: {key_path}")

credentials = service_account.Credentials.from_service_account_file(key_path)
project_id = credentials.project_id
print(f"Project ID from key: {project_id}")

client = bigquery.Client(credentials=credentials, project=project_id)



print("\nChecking access to 'floatchat-472116':")
target_project = "floatchat-472116"
target_dataset = "argo"

try:
    dataset_ref = bigquery.DatasetReference(target_project, target_dataset)
    # Get dataset to check location/existence
    try:
        remote_dataset = client.get_dataset(dataset_ref)
        print(f"Dataset {target_project}.{target_dataset} found.")
        print(f"Location: {remote_dataset.location}")
        
        print(f"Listing tables in {target_project}.{target_dataset}:")
        tables = list(client.list_tables(dataset_ref))
        if tables:
            for table in tables:
                print(f"- {table.table_id}")
        else:
            print("(No tables found)")

    except Exception as e:
        print(f"Could not access dataset {target_project}.{target_dataset}: {e}")

except Exception as e:
    print(f"Error checking target project: {e}")


