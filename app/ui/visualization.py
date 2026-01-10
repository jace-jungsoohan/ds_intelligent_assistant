import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def detect_chart_type(df: pd.DataFrame):
    """
    Analyzes the DataFrame and returns a Plotly figure if a suitable chart type is found.
    Returns: plotly.graph_objects.Figure or None
    """
    if df is None or df.empty:
        return None

    # Normalizing column names for detection
    cols = [c.lower() for c in df.columns]
    
    # 1. Geospatial Analysis (Map)
    # Looking for 'lat', 'lon' or similar
    lat_col = next((c for c in df.columns if 'lat' in c.lower()), None)
    lon_col = next((c for c in df.columns if 'lon' in c.lower() or 'lng' in c.lower()), None)
    
    if lat_col and lon_col:
        # Determine size/color metrics if available
        size_col = next((c for c in df.columns if c.lower() in ['count', 'total', 'risk_score', 'high_impact_events']), None)
        color_col = next((c for c in df.columns if c.lower() in ['risk_score', 'damage_rate', 'avg_shock_g', 'location_label']), None)
        
        fig = px.scatter_mapbox(
            df, 
            lat=lat_col, 
            lon=lon_col,
            size=size_col,
            color=color_col,
            hover_data=df.columns,
            zoom=3 if len(df) > 1 else 10,
            mapbox_style="carto-positron",
            title="Geospatial Analysis"
        )
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        return fig

    # 2. Time Series Analysis (Line Chart)
    # Looking for date/time objects or columns named 'date', 'time', 'day'
    date_col = None
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]) or 'date' in c.lower() or 'time' in c.lower():
            date_col = c
            break
            
    if date_col:
        # Find numeric columns for y-axis
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        # Exclude lat/lon if they were mistakenly identified as metrics
        numeric_cols = [c for c in numeric_cols if 'lat' not in c.lower() and 'lon' not in c.lower()]
        
        if numeric_cols:
            fig = px.line(
                df, 
                x=date_col, 
                y=numeric_cols, 
                markers=True,
                title="Time Series Trends"
            )
            return fig

    # 3. Categorical Comparison (Bar Chart)
    # Look for a string/category column (x-axis) and numeric columns (y-axis)
    cat_col = next((c for c in df.columns if df[c].dtype == 'object' or pd.api.types.is_categorical_dtype(df[c])), None)
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if cat_col and numeric_cols:
        # Sort by first metric for better visualization
        first_metric = numeric_cols[0]
        df_sorted = df.sort_values(by=first_metric, ascending=False).head(20) # Limit to top 20 for readability
        
        fig = px.bar(
            df_sorted,
            x=cat_col,
            y=numeric_cols[0], # Primary metric
            color=numeric_cols[1] if len(numeric_cols) > 1 else None, # Secondary metric as color
            title=f"Comparison by {cat_col}"
        )
        return fig

    return None
