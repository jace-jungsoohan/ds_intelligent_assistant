
from google.cloud import bigquery
from google.api_core.exceptions import NotFound
import sys
import os
from datetime import date, timedelta

# Ensure app is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings

def create_test_data():
    client = bigquery.Client(project=settings.PROJECT_ID, location=settings.BQ_LOCATION)
    dataset_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}"
    
    # 1. Create Dataset if not exists
    try:
        client.get_dataset(dataset_id)
        print(f"Dataset {dataset_id} already exists.")
    except NotFound:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = settings.BQ_LOCATION
        client.create_dataset(dataset)
        print(f"Created dataset {dataset_id}")

    # 2. Create Tables and Insert Data

    # --- view_transport_stats ---
    table_id = f"{dataset_id}.view_transport_stats"
    schema = [
        bigquery.SchemaField("date", "DATE"),
        bigquery.SchemaField("destination", "STRING"),
        bigquery.SchemaField("product", "STRING"),
        bigquery.SchemaField("transport_mode", "STRING"),
        bigquery.SchemaField("transport_path", "STRING"),
        bigquery.SchemaField("total_volume", "INTEGER"),
        bigquery.SchemaField("transport_count", "INTEGER"),
        bigquery.SchemaField("issue_count", "INTEGER"),
    ]
    try:
        client.get_table(table_id)
        print(f"Table {table_id} already exists. Skipping.")
    except NotFound:
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)
        print(f"Created table {table_id}")
        
        # Insert Data
        rows_to_insert = [
            {"date": "2025-12-05", "destination": "Vietnam", "product": "Vaccine", "transport_mode": "Air", "transport_path": "ICN-HAN", "total_volume": 1000, "transport_count": 5, "issue_count": 0},
            {"date": "2025-12-10", "destination": "Vietnam", "product": "Medicine", "transport_mode": "Sea", "transport_path": "PUS-HCM", "total_volume": 5000, "transport_count": 2, "issue_count": 1},
            {"date": "2025-12-20", "destination": "USA", "product": "Food", "transport_mode": "Air", "transport_path": "ICN-LAX", "total_volume": 2000, "transport_count": 10, "issue_count": 0},
            {"date": str(date.today()), "destination": "Vietnam", "product": "Bio", "transport_mode": "Air", "transport_path": "ICN-HAN", "total_volume": 500, "transport_count": 1, "issue_count": 0},
        ]
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            print(f"Encountered errors while inserting rows: {errors}")
        else:
            print(f"Inserted dummy data into {table_id}")


    # --- view_issue_stats ---
    table_id = f"{dataset_id}.view_issue_stats"
    schema = [
        bigquery.SchemaField("transport_mode", "STRING"),
        bigquery.SchemaField("package_type", "STRING"),
        bigquery.SchemaField("destination", "STRING"),
        bigquery.SchemaField("path_segment", "STRING"),
        bigquery.SchemaField("deviation_rate_5g", "FLOAT"),
        bigquery.SchemaField("deviation_rate_10g", "FLOAT"),
        bigquery.SchemaField("cumulative_shock", "FLOAT"),
        bigquery.SchemaField("shock_count", "INTEGER"),
    ]
    try:
        client.get_table(table_id)
        print(f"Table {table_id} already exists. Skipping.")
    except NotFound:
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)
        print(f"Created table {table_id}")
        
        rows = [
            {"transport_mode": "Air", "package_type": "Box", "destination": "Vietnam", "path_segment": "Unloading", "deviation_rate_5g": 0.05, "deviation_rate_10g": 0.01, "cumulative_shock": 15.5, "shock_count": 3},
        ]
        client.insert_rows_json(table_id, rows)
        print(f"Inserted dummy data into {table_id}")

    # --- view_sensor_stats ---
    table_id = f"{dataset_id}.view_sensor_stats"
    schema = [
        bigquery.SchemaField("date", "DATE"),
        bigquery.SchemaField("transport_mode", "STRING"),
        bigquery.SchemaField("destination", "STRING"),
        bigquery.SchemaField("avg_temp", "FLOAT"),
        bigquery.SchemaField("min_temp", "FLOAT"),
        bigquery.SchemaField("max_temp", "FLOAT"),
        bigquery.SchemaField("avg_humidity", "FLOAT"),
        bigquery.SchemaField("shock_alert_count", "INTEGER"),
    ]
    try:
        client.get_table(table_id)
        print(f"Table {table_id} already exists. Skipping.")
    except NotFound:
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)
        print(f"Created table {table_id}")
        
        rows = [
            {"date": "2025-12-15", "transport_mode": "Air", "destination": "Vietnam", "avg_temp": 4.5, "min_temp": 2.1, "max_temp": 8.0, "avg_humidity": 45.0, "shock_alert_count": 0},
        ]
        client.insert_rows_json(table_id, rows)
        print(f"Inserted dummy data into {table_id}")

if __name__ == "__main__":
    create_test_data()
