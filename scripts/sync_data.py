
from google.cloud import bigquery
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings

def sync_mart_views():
    # Use 'US' location because 'scm' dataset might be in US (default) or check locations
    # Based on previous error, 'rag' is in 'asia-northeast3'
    # We need to check 'scm' dataset location first.
    # If they are different, we can't create a view directly joining them if they are in different regions.
    # But Views are virtual.
    
    # Assuming both are compatible or we recreate 'rag' in same region if needed.
    # Let's check 'scm' location first.
    
    client = bigquery.Client(project=settings.PROJECT_ID)
    scm_dataset = client.get_dataset(f"{settings.PROJECT_ID}.scm")
    print(f"SCM Dataset Location: {scm_dataset.location}")
    
    # Update Client to use SCM location for View creation to avoid cross-region issues if possible
    # But 'rag' dataset is in 'asia-northeast3'.
    rag_dataset_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}"
    try:
        rag_dataset = client.get_dataset(rag_dataset_id)
        print(f"RAG Dataset Location: {rag_dataset.location}")
    except:
        print("RAG dataset not found")

    # If locations differ, we might need to recreate RAG dataset in the SAME location as SCM
    if scm_dataset.location != rag_dataset.location:
        print(f"⚠️ Region Mismatch! SCM: {scm_dataset.location}, RAG: {rag_dataset.location}")
        print("Recreating RAG dataset in SCM location...")
        client.delete_dataset(rag_dataset_id, delete_contents=True, not_found_ok=True)
        new_rag = bigquery.Dataset(rag_dataset_id)
        new_rag.location = scm_dataset.location
        client.create_dataset(new_rag)
        print(f"Recreated RAG dataset in {scm_dataset.location}")
    else:
        # If locations match, ensure we delete the dummy tables first
        # because we can't replace a Table with a View directly.
        for table_name in ["view_transport_stats", "view_issue_stats", "view_sensor_stats"]:
            table_id = f"{rag_dataset_id}.{table_name}"
            client.delete_table(table_id, not_found_ok=True)
            print(f"Deleted existing table {table_id} to replace with view.")
    
    # Now create Views
    # 1. view_transport_stats
    q1 = f"""
    CREATE OR REPLACE VIEW `{settings.PROJECT_ID}.{settings.DATASET_ID}.view_transport_stats` AS
    SELECT
      DATE(departure_time) as date,
      pod as destination,
      product_name as product,
      shipmode as transport_mode,
      CONCAT(pol, '-', pod) as transport_path,
      COUNT(*) as total_volume,
      COUNT(*) as transport_count,
      SUM(IFNULL(is_damaged, 0)) as issue_count
    FROM `{settings.PROJECT_ID}.scm.corning_transport`
    GROUP BY 1, 2, 3, 4, 5;
    """
    
    # 2. view_issue_stats
    q2 = f"""
    CREATE OR REPLACE VIEW `{settings.PROJECT_ID}.{settings.DATASET_ID}.view_issue_stats` AS
    SELECT
      'Air' as transport_mode,
      package as package_type,
      pod as destination,
      'Transit' as path_segment,
      AVG(CASE WHEN acc_sum_over5 > 0 THEN 1.0 ELSE 0.0 END) as deviation_rate_5g,
      0.0 as deviation_rate_10g,
      AVG(impact_score_mean) as cumulative_shock,
      SUM(is_damaged_max) as shock_count
    FROM `{settings.PROJECT_ID}.scm.corning_features`
    GROUP BY 1, 2, 3, 4;
    """
    
    # 3. view_sensor_stats
    q3 = f"""
    CREATE OR REPLACE VIEW `{settings.PROJECT_ID}.{settings.DATASET_ID}.view_sensor_stats` AS
    SELECT
      DATE(departure_time) as date,
      shipmode as transport_mode,
      pod as destination,
      AVG((temp_high + temp_low) / 2) as avg_temp,
      AVG(temp_low) as min_temp,
      AVG(temp_high) as max_temp,
      AVG((humid_high + humid_low) / 2) as avg_humidity,
      COUNTIF(alarm_status != 'Normal') as shock_alert_count
    FROM `{settings.PROJECT_ID}.scm.corning_transport`
    GROUP BY 1, 2, 3;
    """

    for name, query in [("view_transport_stats", q1), ("view_issue_stats", q2), ("view_sensor_stats", q3)]:
        print(f"Creating view: {name}...")
        try:
            client.query(query).result()
            print(f"✅ {name} synced with real data.")
        except Exception as e:
            print(f"❌ Failed to create {name}: {e}")

if __name__ == "__main__":
    sync_mart_views()
