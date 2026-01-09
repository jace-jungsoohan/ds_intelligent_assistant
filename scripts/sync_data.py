
from google.cloud import bigquery
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings

def sync_mart_tables():
    """
    Creates Materialized Mart Tables in RAG dataset.
    
    Data Sources:
    1. view_transport_stats -> rag.corning_transport (Master transport data)
    2. view_issue_stats     -> rag.corning_merged (Detailed sensor/shock logs)
    3. view_sensor_stats    -> rag.corning_merged (Detailed sensor timeseries)
    """
    client = bigquery.Client(project=settings.PROJECT_ID)
    dataset_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}"
    
    print(f"Building Scalable Mart Tables in: {dataset_id}")
    
    # Check dataset existence
    try:
        client.get_dataset(dataset_id)
    except:
        print(f"Error: Dataset {dataset_id} not found.")
        return

    # 1. Transport Stats
    # Source: corning_transport (Efficient for counting total shipments)
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
    
    # 2. Issue Stats
    # Source: corning_merged (Has direct 'acc_over5', 'acc_over10', 'shock_high' fields)
    q2 = f"""
    CREATE OR REPLACE TABLE `{dataset_id}.view_issue_stats`
    CLUSTER BY destination
    AS
    SELECT
      shipmode as transport_mode,
      package as package_type,
      pod as destination,
      'End-to-End' as path_segment,
      
      -- Calculate rates based on unique shipments having issues
      -- We group by shipment code first to see if it had any issue
      COUNTIF(max_acc_over5 > 0) / COUNT(*) as deviation_rate_5g,
      COUNTIF(max_acc_over10 > 0) / COUNT(*) as deviation_rate_10g,
      
      AVG(max_shock) as cumulative_shock,
      SUM(CASE WHEN max_shock > 0 THEN 1 ELSE 0 END) as shock_count
      
    FROM (
        SELECT 
            code, shipmode, package, pod,
            MAX(acc_over5) as max_acc_over5,
            MAX(acc_over10) as max_acc_over10,
            MAX(shock_high) as max_shock
        FROM `{dataset_id}.corning_merged`
        GROUP BY 1, 2, 3, 4
    )
    GROUP BY 1, 2, 3, 4;
    """
    
    # 3. Sensor Stats
    # Source: corning_merged (Real timeseries temperature/humidity data)
    q3 = f"""
    CREATE OR REPLACE TABLE `{dataset_id}.view_sensor_stats`
    PARTITION BY date
    CLUSTER BY destination
    AS
    SELECT
      DATE(device_datetime) as date,
      shipmode as transport_mode,
      pod as destination,
      
      AVG(temperature) as avg_temp,
      MIN(temperature) as min_temp,
      MAX(temperature) as max_temp,
      AVG(humidity) as avg_humidity,
      
      COUNTIF(alarm_status != 'Normal') as shock_alert_count
      
    FROM `{dataset_id}.corning_merged`
    WHERE device_datetime IS NOT NULL
    GROUP BY 1, 2, 3;
    """

    # Execute
    for name, query in [("view_transport_stats", q1), ("view_issue_stats", q2), ("view_sensor_stats", q3)]:
        print(f"Building table: {name}...")
        try:
            client.query(query).result()
            print(f"✅ {name} built successfully.")
            
            verify_q = f"SELECT COUNT(*) as cnt FROM `{dataset_id}.{name}`"
            df = client.query(verify_q).to_dataframe()
            print(f"   -> Rows: {df['cnt'][0]}")
            
        except Exception as e:
            print(f"❌ Failed to build {name}: {e}")

if __name__ == "__main__":
    sync_mart_tables()
