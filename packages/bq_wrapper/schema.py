
from typing import Dict, List

# Define the schema for the tables as we expect them to exist in BigQuery
# consistent with the PDF requirements.

TABLE_SCHEMAS: Dict[str, str] = {
    "view_transport_stats": """
    CREATE TABLE view_transport_stats (
        date DATE,
        destination STRING,
        product STRING,
        transport_mode STRING,
        transport_path STRING,
        total_volume INT64,
        transport_count INT64,
        issue_count INT64
    );
    -- Description: Contains daily transport volume and issue counts aggregated by destination, product, and mode.
    """,
    "view_issue_stats": """
    CREATE TABLE view_issue_stats (
        transport_mode STRING,
        package_type STRING,
        destination STRING,
        path_segment STRING,
        deviation_rate_5g FLOAT64,
        deviation_rate_10g FLOAT64,
        cumulative_shock FLOAT64,
        shock_count INT64
    );
    -- Description: Aggregated statistics on transport issues, including deviation rates (shocks > 5G/10G) and shock counts.
    """,
    "view_sensor_stats": """
    CREATE TABLE view_sensor_stats (
        date DATE,
        transport_mode STRING,
        destination STRING,
        avg_temp FLOAT64,
        min_temp FLOAT64,
        max_temp FLOAT64,
        avg_humidity FLOAT64,
        shock_alert_count INT64
    );
    -- Description: Summary of sensor data (temperature, humidity) and shock alerts for transport conditions.
    """
}

def get_table_info() -> str:
    """Returns the formatted schema information for the LLM."""
    info = ""
    for table_name, schema in TABLE_SCHEMAS.items():
        info += f"Table: {table_name}\n{schema}\n\n"
    return info
