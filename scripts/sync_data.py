
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
    
    # 2. Mart Sensor Detail
    q_detail = f"""
    CREATE OR REPLACE TABLE `{dataset_id}.mart_sensor_detail`
    PARTITION BY event_date
    CLUSTER BY destination, code
    AS
    SELECT
        DATE(device_datetime) as event_date,
        device_datetime as event_timestamp,
        code,
        pod as destination,
        
        temperature,
        humidity,
        shock_high as shock_g,
        
        acc as acc_resultant,
        accx as acc_x,
        accy as acc_y,
        accz as acc_z,
        tiltx as tilt_x,
        tilty as tilt_y,
        
        lat,
        lon,
        
        CASE 
            WHEN acc < 0.2 THEN 'Static'
            ELSE 'Moving'
        END as status
        
    FROM `{dataset_id}.corning_merged`
    WHERE device_datetime IS NOT NULL;
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

    tasks = [
        ("mart_logistics_master", q_master),
        ("mart_sensor_detail", q_detail),
        ("mart_risk_heatmap", q_heatmap),
        ("mart_quality_matrix", q_matrix)
    ]

    for name, query in tasks:
        print(f"🏗️ Building {name}...")
        try:
            client.query(query).result()
            print(f"✅ {name} built successfully.")
            
            df = client.query(f"SELECT COUNT(*) as cnt FROM `{dataset_id}.{name}`").to_dataframe()
            print(f"   -> Rows: {df['cnt'][0]}")
            
        except Exception as e:
            print(f"❌ Failed to build {name}: {e}")

if __name__ == "__main__":
    sync_whitepaper_mart()
