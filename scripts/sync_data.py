
from google.cloud import bigquery
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings

def sync_mart_tables():
    """
    Creates Materialized Mart Tables in RAG dataset for Scalability.
    Uses Partitioning (by Date) and Clustering (by Destination) to optimize cost and performance.
    """
    client = bigquery.Client(project=settings.PROJECT_ID)
    dataset_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}"
    
    print(f"Building Scalable Mart Tables in: {dataset_id}")
    
    # 1. Transport Stats Table
    # Strategy: Partition by Date, Cluster by Destination & Product
    q1 = f"""
    CREATE OR REPLACE TABLE `{dataset_id}.view_transport_stats`
    PARTITION BY date
    CLUSTER BY destination, product
    AS
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
    WHERE departure_time IS NOT NULL
    GROUP BY 1, 2, 3, 4, 5;
    """
    
    # 2. Issue Stats Table
    # Strategy: Since this is a high-level summary without date, we Cluster by Destination.
    # (Optional: We could add a 'snapshot_date' partition if historical tracking is needed)
    q2 = f"""
    CREATE OR REPLACE TABLE `{dataset_id}.view_issue_stats`
    CLUSTER BY destination
    AS
    SELECT
      shipmode as transport_mode,
      package as package_type,
      pod as destination,
      'End-to-End' as path_segment,
      
      COUNTIF(SAFE_CAST(shock_high AS FLOAT64) >= 5.0) / COUNT(*) as deviation_rate_5g,
      COUNTIF(SAFE_CAST(shock_high AS FLOAT64) >= 10.0) / COUNT(*) as deviation_rate_10g,
      AVG(SAFE_CAST(shock_high AS FLOAT64)) as cumulative_shock,
      COUNTIF(SAFE_CAST(shock_high AS FLOAT64) > 0) as shock_count
      
    FROM `{dataset_id}.corning_transport`
    GROUP BY 1, 2, 3, 4;
    """
    
    # 3. Sensor Stats Table
    # Strategy: Partition by Date, Cluster by Destination (Optimized for time-series lookup)
    q3 = f"""
    CREATE OR REPLACE TABLE `{dataset_id}.view_sensor_stats`
    PARTITION BY date
    CLUSTER BY destination
    AS
    SELECT
      DATE(departure_time) as date,
      shipmode as transport_mode,
      pod as destination,
      
      AVG((SAFE_CAST(temp_high AS FLOAT64) + SAFE_CAST(temp_low AS FLOAT64)) / 2) as avg_temp,
      AVG(SAFE_CAST(temp_low AS FLOAT64)) as min_temp,
      AVG(SAFE_CAST(temp_high AS FLOAT64)) as max_temp,
      AVG((SAFE_CAST(humid_high AS FLOAT64) + SAFE_CAST(humid_low AS FLOAT64)) / 2) as avg_humidity,
      
      COUNTIF(alarm_status != 'Normal') as shock_alert_count
      
    FROM `{dataset_id}.corning_transport`
    WHERE departure_time IS NOT NULL
    GROUP BY 1, 2, 3;
    """

    # Execute
    for name, query in [("view_transport_stats", q1), ("view_issue_stats", q2), ("view_sensor_stats", q3)]:
        print(f"Building table: {name}...")
        try:
            # Drop VIEW if exists (Cannot create TABLE over VIEW with same name)
            client.delete_table(f"{dataset_id}.{name}", not_found_ok=True)
            
            client.query(query).result()
            print(f"✅ {name} built successfully (Partitioned/Clustered Table).")
            
            # Verify rows
            verify_q = f"SELECT COUNT(*) as cnt FROM `{dataset_id}.{name}`"
            df = client.query(verify_q).to_dataframe()
            print(f"   -> Rows: {df['cnt'][0]}")
            
        except Exception as e:
            print(f"❌ Failed to build {name}: {e}")

if __name__ == "__main__":
    sync_mart_tables()
