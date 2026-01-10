
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
- Shanghai, Sanghai, 상해, 상하이, SH -> 'CNSHG'
- Osaka, Osaca, 오사카, 오사카항 -> 'JPOSA'
- Rizhao, Rizo, 일조, 리자오 -> 'CNRZH'
- Lianyungang, Lianyun, 연운항 -> 'CNLYG'
- Ningbo, Ningpo, 닝보 -> 'CNNBG'
- Hochiminh, HCMC, 호치민 -> 'VNSGN' (or like '%VN%')
- Haiphong, 하이퐁 -> 'VNHPH'
- Incheon, ICN, 인천 -> 'KRICN'
- Busan, Pusan, 부산 -> 'KRPUS'

Example SQLs (Few-shot Learning):
Example SQLs (Few-shot Learning):
1. "🛳️ 해상 운송 중 5G 이상 충격 발생 비율" (Ratio Calculation)
SELECT
    t2.transport_mode,
    COUNTIF(t1.shock_g >= 5) as high_shock_count,
    COUNT(*) as total_sensor_readings,
    SAFE_DIVIDE(COUNTIF(t1.shock_g >= 5), COUNT(*)) as high_shock_ratio
FROM `willog-prod-data-gold.rag.mart_sensor_detail` t1
JOIN `willog-prod-data-gold.rag.mart_logistics_master` t2 ON t1.code = t2.code
WHERE t2.transport_mode = 'Ocean' -- Optional: Remove WHERE to see all modes
GROUP BY 1

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
    AND t1.shock_g > 0 
    AND t1.event_date BETWEEN DATE_TRUNC(CURRENT_DATE(), MONTH) AND CURRENT_DATE()

4. "❄️ 60분이상 지속된 영하 온도에서 발생한 충격 건수" (Duration + Complex Condition)
-- 'Duration' queries usually refer to 'temp_excursion_duration_min' in master table.
SELECT
    COUNT(*) as shock_count
FROM `willog-prod-data-gold.rag.mart_sensor_detail` t1
JOIN `willog-prod-data-gold.rag.mart_logistics_master` t2 ON t1.code = t2.code
WHERE
    t1.temperature < 0
    AND t2.temp_excursion_duration_min >= 60 -- Use pre-calculated duration from master
    AND t1.shock_g > 0

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
        
        print(f"DEBUG: Generated SQL for '{question}': [{generated_sql}]") # Debug log
        
        clean_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
        
        if not clean_sql:
            return {
                "question": question,
                "generated_sql": "",
                "result": None,
                "natural_response": "SQL 생성 실패: 질문을 이해하지 못했습니다.",
                "error": "Empty SQL generated"
            }
        
        # 2. Execute SQL against BigQuery
        result_df = None
        error = None
        try:
            if bq_client.client:
                print(f"DEBUG: Executing query on BigQuery...")
                result_df = bq_client.run_query(clean_sql)
                print(f"DEBUG: Query executed. Result shape: {result_df.shape if result_df is not None else 'None'}")
            else:
                error = "BigQuery Client is not initialized (client object is None)."
                print(f"DEBUG: {error}")
        except Exception as e:
            error = str(e)
            print(f"DEBUG: Query execution failed: {error}")

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
            # Fallback for unexpected None result without explicit error
            natural_response = (
                f"⚠️ 데이터 조회에 실패했습니다.\n"
                f"SQL은 생성되었으나 BigQuery 실행 결과를 받아오지 못했습니다.\n"
                f"디버그 정보:\n"
                f"- SQL: `{clean_sql}`\n"
                f"- BQ Client Status: {'Active' if bq_client.client else 'Inactive'}"
            )

        return {
            "question": question,
            "generated_sql": clean_sql,
            "result": result_df,
            "natural_response": natural_response,
            "error": error
        }

agent = SQLAgent()
