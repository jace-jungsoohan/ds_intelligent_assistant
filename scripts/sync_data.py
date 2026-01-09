
from google.cloud import bigquery
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings

def sync_rag_views():
    """
    Creates Views in RAG dataset using ONLY 'rag.corning_transport'.
    Fixes data type issues with explicit CASTing.
    """
    client = bigquery.Client(project=settings.PROJECT_ID)
    dataset_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}"
    
    print(f"Syncing views using source: {dataset_id}.corning_transport")
    
    # Check dataset existence
    try:
        client.get_dataset(dataset_id)
    except:
        print(f"Error: Dataset {dataset_id} not found.")
        return

    # 1. Clean up existing objects
    for table_name in ["view_transport_stats", "view_issue_stats", "view_sensor_stats"]:
        client.delete_table(f"{dataset_id}.{table_name}", not_found_ok=True)

    # 2. View: Transport Stats
    # Casting 'is_damaged' to INT64 to define issue count
    q1 = f"""
    CREATE OR REPLACE VIEW `{dataset_id}.view_transport_stats` AS
    SELECT
      DATE(departure_time) as date,
      pod as destination,
      product_name as product,
      shipmode as transport_mode,
      CONCAT(pol, '-', pod) as transport_path,
      COUNT(*) as total_volume,
      COUNT(*) as transport_count,
      COUNTIF(SAFE_CAST(is_damaged AS INT64) > 0) as issue_count
    FROM `{dataset_id}.corning_transport`
    GROUP BY 1, 2, 3, 4, 5;
    """
    
    # 3. View: Issue Stats (Derived from corning_transport instead of features)
    # Using 'shock_high' or 'is_damaged' as proxies for statistics
    q2 = f"""
    CREATE OR REPLACE VIEW `{dataset_id}.view_issue_stats` AS
    SELECT
      shipmode as transport_mode,
      package as package_type,
      pod as destination,
      'End-to-End' as path_segment,
      
      -- Calculate 5G deviation rate (Assuming shock_high > 5 is an issue)
      COUNTIF(SAFE_CAST(shock_high AS FLOAT64) >= 5.0) / COUNT(*) as deviation_rate_5g,
      
      -- 10G deviation rate
      COUNTIF(SAFE_CAST(shock_high AS FLOAT64) >= 10.0) / COUNT(*) as deviation_rate_10g,
      
      -- Avg shock
      AVG(SAFE_CAST(shock_high AS FLOAT64)) as cumulative_shock,
      
      -- Total shock count (events > 0)
      COUNTIF(SAFE_CAST(shock_high AS FLOAT64) > 0) as shock_count
      
    FROM `{dataset_id}.corning_transport`
    GROUP BY 1, 2, 3, 4;
    """
    
    # 4. View: Sensor Stats
    # Casting temp/humidity columns safely before aggregation
    q3 = f"""
    CREATE OR REPLACE VIEW `{dataset_id}.view_sensor_stats` AS
    SELECT
      DATE(departure_time) as date,
      shipmode as transport_mode,
      pod as destination,
      
      -- Safe CAST and Aggregation
      AVG((SAFE_CAST(temp_high AS FLOAT64) + SAFE_CAST(temp_low AS FLOAT64)) / 2) as avg_temp,
      AVG(SAFE_CAST(temp_low AS FLOAT64)) as min_temp,
      AVG(SAFE_CAST(temp_high AS FLOAT64)) as max_temp,
      AVG((SAFE_CAST(humid_high AS FLOAT64) + SAFE_CAST(humid_low AS FLOAT64)) / 2) as avg_humidity,
      
      -- Alert count
      COUNTIF(alarm_status != 'Normal') as shock_alert_count
      
    FROM `{dataset_id}.corning_transport`
    GROUP BY 1, 2, 3;
    """

    # Execute
    for name, query in [("view_transport_stats", q1), ("view_issue_stats", q2), ("view_sensor_stats", q3)]:
        print(f"Creating view: {name}...")
        try:
            client.query(query).result()
            print(f"✅ {name} created.")
            
            # Verify
            try:
                cnt_df = client.query(f"SELECT COUNT(*) as cnt FROM `{dataset_id}.{name}`").to_dataframe()
                print(f"   -> Verified rows: {cnt_df['cnt'][0]}")
            except Exception as ve:
                print(f"   ⚠️ Created but empty/error: {ve}")
                
        except Exception as e:
            print(f"❌ Failed to create {name}: {e}")

if __name__ == "__main__":
    sync_rag_views()
