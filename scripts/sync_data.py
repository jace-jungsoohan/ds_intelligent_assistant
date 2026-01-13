
from google.cloud import bigquery
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings

def sync_whitepaper_mart():
    """
    Builds the Advanced Data Mart defined in the Whitepaper.
    FIXED: Syntax errors in BigQuery SQL (Comment interference, alias visibility).
    """
    client = bigquery.Client(project=settings.PROJECT_ID)
    dataset_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}"
    
    print(f"🚀 Building Whitepaper Data Mart in: {dataset_id}")
    
    # Check dataset existence
    try:
        client.get_dataset(dataset_id)
    except:
        print(f"Error: Dataset {dataset_id} not found.")
        return

    # Drop existing tables to avoid clustering spec conflicts
    tables_to_drop = ["mart_sensor_detail"]  # Tables with changed clustering
    for table_name in tables_to_drop:
        try:
            client.delete_table(f"{dataset_id}.{table_name}", not_found_ok=True)
            print(f"🗑️ Dropped existing table: {table_name}")
        except Exception as e:
            print(f"Warning: Could not drop {table_name}: {e}")

    # 1. Mart Logistics Master
    q_master = f"""
    CREATE OR REPLACE TABLE `{dataset_id}.mart_logistics_master`
    PARTITION BY departure_date
    CLUSTER BY destination, product, risk_level
    AS
    WITH sensor_metrics AS (
        SELECT 
            code,
            -- Cumulative Fatigue
            SUM(CASE WHEN shock_high > 2 THEN POW(shock_high, 1.5) ELSE 0 END) as cumulative_shock_index,
            MAX(shock_high) as max_shock_g,
            AVG(shock_high) as avg_shock_g,
            -- Excursions (Multiplying count by 10 for minutes, assuming 10min interval)
            (COUNTIF(temperature < 0 OR temperature > 25) * 10) as temp_excursion_duration_est_min
        FROM `{dataset_id}.corning_merged`
        GROUP BY 1
    )
    SELECT
      DATE(t.departure_time) as departure_date,
      t.code,
      t.pol,
      t.pod as destination,
      t.product_name as product,
      t.package as package_type,
      t.shipmode as transport_mode,
      t.receiver_name as receive_name,
      DATE(t.arrival_time) as arrival_date,
      
      c.filter as category_filter,
      
      COALESCE(s.cumulative_shock_index, 0) as cumulative_shock_index,
      COALESCE(s.max_shock_g, 0) as max_shock_g,
      COALESCE(s.avg_shock_g, 0) as avg_shock_g,
      COALESCE(s.temp_excursion_duration_est_min, 0) as temp_excursion_duration_min,
      
      t.is_damaged,
      
      CASE 
        WHEN t.is_damaged THEN 'Critical'
        WHEN s.cumulative_shock_index > 500 OR s.temp_excursion_duration_est_min > 60 THEN 'High'
        WHEN s.max_shock_g > 8 THEN 'Medium'
        ELSE 'Low'
      END as risk_level
      
    FROM `{dataset_id}.corning_transport` t
    LEFT JOIN sensor_metrics s ON t.code = s.code
    LEFT JOIN `{dataset_id}.view_category` c ON t.code = c.code 
    WHERE t.departure_time IS NOT NULL;
    """
    
    # 2. Mart Sensor Detail (Enhanced with transport_mode for easier queries)
    q_detail = f"""
    CREATE OR REPLACE TABLE `{dataset_id}.mart_sensor_detail`
    PARTITION BY event_date
    CLUSTER BY destination, transport_mode, code
    AS
    SELECT
        DATE(m.device_datetime) as event_date,
        m.device_datetime as event_timestamp,
        m.code,
        m.pod as destination,
        -- Added: Country code extraction for easier filtering
        CASE 
            WHEN m.pod LIKE 'CN%' THEN 'China'
            WHEN m.pod LIKE 'JP%' THEN 'Japan'
            WHEN m.pod LIKE 'VN%' THEN 'Vietnam'
            WHEN m.pod LIKE 'KR%' THEN 'Korea'
            WHEN m.pod LIKE 'US%' THEN 'USA'
            ELSE 'Other'
        END as destination_country,
        -- Added: Transport mode from master for direct queries
        t.shipmode as transport_mode,
        t.receiver_name as receive_name,
        
        m.temperature,
        m.humidity,
        m.shock_high as shock_g,
        
        m.acc as acc_resultant,
        m.accx as acc_x,
        m.accy as acc_y,
        m.accz as acc_z,
        m.tiltx as tilt_x,
        m.tilty as tilt_y,
        
        m.lat,
        m.lon,
        
        CASE 
            WHEN m.acc < 0.2 THEN 'Static'
            ELSE 'Moving'
        END as status
        
    FROM `{dataset_id}.corning_merged` m
    LEFT JOIN `{dataset_id}.corning_transport` t ON m.code = t.code
    WHERE m.device_datetime IS NOT NULL;
    """
    
    # 3. Mart Risk Heatmap
    q_heatmap = f"""
    CREATE OR REPLACE TABLE `{dataset_id}.mart_risk_heatmap`
    CLUSTER BY location_label
    AS
    SELECT
        ROUND(lat, 2) as lat_center,
        ROUND(lon, 2) as lon_center,
        ANY_VALUE(location) as location_label,
        
        COUNT(*) as total_logs,
        AVG(shock_high) as avg_shock_intensity,
        MAX(shock_high) as max_shock_intensity,
        COUNTIF(shock_high > 5) as high_impact_events,
        
        (COUNTIF(shock_high > 5) / COUNT(*)) * AVG(shock_high) as risk_score
        
    FROM `{dataset_id}.corning_merged`
    WHERE lat IS NOT NULL AND lon IS NOT NULL
    GROUP BY 1, 2
    HAVING total_logs > 10;
    """
    
    # 4. Mart Quality Matrix
    q_matrix = f"""
    CREATE OR REPLACE TABLE `{dataset_id}.mart_quality_matrix`
    AS
    SELECT
        transport_mode,
        package_type,
        CONCAT(pol, '-', destination) as route,
        
        COUNT(*) as total_shipments,
        countif(is_damaged) / count(*) as damage_rate,
        
        AVG(cumulative_shock_index) as avg_fatigue_score,
        
        100 - (countif(risk_level = 'High' OR risk_level = 'Critical') / count(*) * 100) as safety_score
        
    FROM `{dataset_id}.mart_logistics_master`
    GROUP BY 1, 2, 3;
    """

    # Define tasks as a list of dictionaries for better extensibility
    tasks = [
        {
            "table_name": "mart_logistics_master",
            "query": q_master,
            "description": "Master Shipment Facts"
        },
        {
            "table_name": "mart_sensor_detail", 
            "query": q_detail,
            "description": "Granular Sensor Logs"
        },
        {
            "table_name": "mart_risk_heatmap",
            "query": q_heatmap,
            "description": "Geospatial Aggregations"
        },
        {
            "table_name": "mart_quality_matrix",
            "query": q_matrix,
            "description": "Performance Benchmarking"
        }
    ]

    for task in tasks:
        name = task["table_name"]
        query = task["query"]
        desc = task["description"]
        
        print(f"🏗️ Building {name} ({desc})...")
        try:
            client.query(query).result()
            print(f"✅ {name} built successfully.")
            
            df = client.query(f"SELECT COUNT(*) as cnt FROM `{dataset_id}.{name}`").to_dataframe()
            print(f"   -> Rows: {df['cnt'][0]}")
            
        except Exception as e:
            print(f"❌ Failed to build {name}: {e}")

if __name__ == "__main__":
    sync_whitepaper_mart()
