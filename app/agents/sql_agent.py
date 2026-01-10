
from typing import Any, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_google_vertexai import ChatVertexAI
from app.core.config import settings
from packages.bq_wrapper.schema import get_table_info
from packages.bq_wrapper.client import BigQueryWrapper




# Initialize Vertex AI Chat Model
# Ensure your environment has Google Cloud credentials set up

try:



    llm = ChatVertexAI(
        model_name="gemini-2.5-flash",
        project=settings.PROJECT_ID,
        location=settings.LOCATION,
        temperature=0,
        max_output_tokens=2048
    )
except Exception as e:
    print(f"Warning: Could not initialize Vertex AI: {e}")
    llm = None

bq_client = BigQueryWrapper()

# 1. SQL Generation Step
template_sql_gen = """
You are a BigQuery expert for a logistics company named Willog.
Your goal is to answer user questions by generating a valid Standard SQL query.

Dataset: `willog-prod-data-gold.rag`

Available tables (always use fully qualified names with backticks):

1. `willog-prod-data-gold.rag.mart_logistics_master` (Fact Table)
   - Purpose: Master transport stats, volume, damage rates, RISK LEVELS, FATIGUE.
   - Columns: 
     - code (STRING): Shipment ID
     - departure_date (DATE): Partition Key
     - destination (STRING), product (STRING), transport_mode (STRING)
     - cumulative_shock_index (FLOAT): "Fatigue" or "Cumulative Stress" score
     - risk_level (STRING): 'Low', 'Medium', 'High', 'Critical'
     - temp_excursion_duration_min (INT64): Minutes outside valid temp range
     - is_damaged (BOOL): Damage flag

2. `willog-prod-data-gold.rag.mart_sensor_detail` (Big Data / Granular)
   - Purpose: Dynamic Threshold Queries (e.g. "Shock > 7G"), Multi-variable Correlation, Directional Analysis.
   - Columns: event_date, shock_g, temperature, humidity, acc_x, acc_y, acc_z, tilt_x, tilt_y, lat, lon

3. `willog-prod-data-gold.rag.mart_risk_heatmap` (Geospatial)
   - Purpose: "Heatmap", "Risk Map", "Where do shocks occur?".
   - Columns: lat_center, lon_center, location_label, risk_score, high_impact_events

4. `willog-prod-data-gold.rag.mart_quality_matrix` (Benchmarking)
   - Purpose: Compare Performance (A vs B), Benchmarking Packaging/Routes.
   - Columns: transport_mode, package_type, route, damage_rate, avg_fatigue_score, safety_score

Scenario Guidelines (Whitepaper Analytics):
- **Fatigue/Stress**: Query `cumulative_shock_index` from `mart_logistics_master`.
- **Benchmarking/Comparison**: Query `mart_quality_matrix`.
- **Composite Conditions (e.g. Temp < 0 & Shock > 5)**: Query `mart_sensor_detail`.
- **Location filtering for Sensor Data**: You MUST JOIN `mart_sensor_detail` (t1) with `mart_logistics_master` (t2) on `t1.code = t2.code` to filter by `destination` (e.g., 'China', 'Vietnam'). `mart_sensor_detail` only has lat/lon, NOT destination name.

Code Mapping Guide (Interpret location names as follows):
- Shanghai, Sanghai, 상해, 상하이 -> 'CNSHG'
- Osaka, 오사카 -> 'JPOSA'
- Rizhao, 일조, 리자오 -> 'CNRZH'
- Lianyungang, 연운항 -> 'CNLYG'
- Ningbo, 닝보 -> 'CNNBG'

Example SQLs (Few-shot Learning):
1. "해상 운송 중 5G 이상 충격 발생 비율" (Ratio Calculation)
SELECT
    'Ocean' as transport_mode,
    COUNTIF(shock_g >= 5) as high_shock_count,
    COUNT(*) as total_count,
    SAFE_DIVIDE(COUNTIF(shock_g >= 5), COUNT(*)) as high_shock_ratio
FROM `willog-prod-data-gold.rag.mart_sensor_detail`

2. "베트남행 화물 중 습도 이탈 구간" (Route/Location Analysis)
SELECT lat, lon, COUNT(*) as excursion_count
FROM `willog-prod-data-gold.rag.mart_sensor_detail`
WHERE destination LIKE '%VN%' OR destination = 'VNSGN' -- ERROR: Destination not in sensor_detail
-- CORRECT APPROACH:
-- SELECT t1.lat, t1.lon, COUNT(*) 
-- FROM `willog-prod-data-gold.rag.mart_sensor_detail` t1
-- JOIN `willog-prod-data-gold.rag.mart_logistics_master` t2 ON t1.code = t2.code
-- WHERE t2.destination LIKE '%VN%' ...

3. "이번 달 중국에서 영하 온도 충격 건수" (Location + Sensor Condition)
SELECT
    COUNT(*) as shock_count_below_zero
FROM `willog-prod-data-gold.rag.mart_sensor_detail` t1
JOIN `willog-prod-data-gold.rag.mart_logistics_master` t2 ON t1.code = t2.code
WHERE
    t2.destination LIKE '%China%' OR t2.destination IN ('CNSHG', 'CNNBG', 'CNRZH', 'CNLYG')
    AND t1.temperature < 0
    AND t1.shock_g > 0 -- Assuming 'shock event' means strict shock > 0 or a threshold like > 2
    AND t1.event_date BETWEEN DATE_TRUNC(CURRENT_DATE(), MONTH) AND CURRENT_DATE()

Question: {question}
SQL Query:
"""

prompt_sql_gen = ChatPromptTemplate.from_template(template_sql_gen)

def get_schema(_):
    return get_table_info()



if llm:
    sql_generator_chain = (
        prompt_sql_gen
        | llm
        | StrOutputParser()
    )
else:
    # Mock chain if LLM is not available
    class MockSQLChain:
        def invoke(self, input_dict):
            return "```sql\n-- Mock SQL (LLM unavailable)\nSELECT * FROM view_transport_stats LIMIT 10\n```"
    sql_generator_chain = MockSQLChain()

# 2. Response Synthesis Prompt
template_synthesis = """
You are a helpful assistant for Willog logistics.
Based on the SQL query result, provide a natural language answer to the user's question.
Answer in Korean (한국어).

User Question: {question}
SQL Query: {sql}
Query Result: {result}

If the result is empty, say "해당 조건에 맞는 데이터가 없습니다."
Keep the answer concise and informative.

Answer:
"""

prompt_synthesis = ChatPromptTemplate.from_template(template_synthesis)

if llm:
    synthesis_chain = prompt_synthesis | llm | StrOutputParser()
else:
    synthesis_chain = None

class SQLAgent:
    def __init__(self):
        self.chain = sql_generator_chain
        self.synthesis_chain = synthesis_chain
    
    def process_query(self, question: str) -> Dict[str, Any]:
        from datetime import date
        current_date = date.today().isoformat()
        
        # 1. Generate SQL
        generated_sql = self.chain.invoke({
            "question": question, 
            "current_date": current_date
        })
        
        clean_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
        
        # 2. Execute SQL against BigQuery
        result_df = None
        error = None
        try:
            if bq_client.client:
                result_df = bq_client.run_query(clean_sql)
        except Exception as e:
            error = str(e)

        # 3. Synthesize natural language response
        natural_response = None
        if result_df is not None and self.synthesis_chain:
            try:
                # Convert DataFrame to string for LLM
                result_str = result_df.to_string() if not result_df.empty else "(empty)"
                natural_response = self.synthesis_chain.invoke({
                    "question": question,
                    "sql": clean_sql,
                    "result": result_str
                })
            except Exception as e:
                natural_response = f"결과 해석 중 오류: {e}"
        elif error:
            natural_response = f"쿼리 실행 중 오류가 발생했습니다: {error}"
        elif result_df is None:
            natural_response = f"생성된 SQL:\n{clean_sql}\n\n(BigQuery 연결이 필요합니다)"

        return {
            "question": question,
            "generated_sql": clean_sql,
            "result": result_df,
            "natural_response": natural_response,
            "error": error
        }

agent = SQLAgent()
