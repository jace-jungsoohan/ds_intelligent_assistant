
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
 
**Failure Handling**:
- If the user's question is ambiguous (e.g., uses undefined terms like "배송 건수" without context) or requires more details (e.g., "Show me data" without date/route), do NOT generate SQL.
- Instead, output: `CLARIFICATION_NEEDED: <Reason and Question to user>`
- Example: `CLARIFICATION_NEEDED: "배송 건수"가 정확히 어떤 의미인가요? '출고 건수'(출발 기준)인가요, 아니면 '운송 건수'(운송 중 포함)인가요?`

**IMPORTANT**: You must use the FULLY QUALIFIED TABLE NAMES provided below (e.g. `willog-prod-data-gold.rag.mart_logistics_master`). NEVER use placeholders like `your_table_name` or `dataset.table`.

Available tables (always use fully qualified names with backticks):

1. `willog-prod-data-gold.rag.mart_logistics_master` (Fact Table)
   - Purpose: Master transport stats, volume, damage rates, RISK LEVELS, FATIGUE.
   - Columns: 
     - code (STRING): Shipment ID
     - departure_date (DATE): Partition Key - use for time filtering (e.g., "이번 달", "최근 1주일")
     - arrival_date (DATE): Arrival Date (CRITICAL for "운송 건수" / active shipments queries)
     - destination (STRING): Port code (e.g., 'CNSHG')
     - product (STRING)
     - transport_mode (STRING): 'air', 'truck', 'ocean+ferry', 'ocean+rail' (Note: Raw data is lowercase. 'ocean' often appears in composites.)
     - package_type (STRING): Packaging type
     - cumulative_shock_index (FLOAT): "Fatigue" or "Cumulative Stress" score
     - risk_level (STRING): 'Low', 'Medium', 'High', 'Critical'
     - temp_excursion_duration_min (INT64): Minutes outside valid temp range
     - is_damaged (BOOL): Damage flag
     - receive_name (STRING): Transport Route Name (Mapped from 'receiver_name'). e.g. 'Customer A'. Use for "운송경로".

2. `willog-prod-data-gold.rag.mart_sensor_detail` (Big Data / Granular)
   - Purpose: Dynamic Threshold Queries (e.g. "Shock > 7G"), Multi-variable Correlation, Directional Analysis.
   - Columns: 
     - event_date (DATE): Partition Key - use for time filtering
     - event_timestamp (TIMESTAMP)
     - code (STRING): Shipment ID (Join Key)
     - destination (STRING): Destination port code.
     - location_fin_corrected (STRING): Transport Segment / Corrected Location Name. Use for "운송구간".
     - destination_country (STRING): 'China', 'Japan', 'Vietnam', 'Korea', 'USA', 'Other'
     - transport_mode (STRING): Copied from master.
     - shock_g (FLOAT), temperature (FLOAT), humidity (FLOAT)
     - acc_x, acc_y, acc_z (FLOAT): Directional acceleration
     - tilt_x, tilt_y (FLOAT): Tilt angles
     - lat, lon (FLOAT): Geolocation

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
- **Country filtering**: Use `destination_country` in `mart_sensor_detail` (e.g., WHERE destination_country = 'China').
- **Transport Mode**: Use LOWERCASE values ('ocean', 'air', 'truck') or `LIKE` for safety (e.g. `WHERE transport_mode LIKE 'ocean%'`).
- **Time filtering**: Use `departure_date` or `event_date` with DATE functions:
  - "이번 달": `WHERE event_date >= DATE_TRUNC(CURRENT_DATE(), MONTH)`
  - "최근 1주일": `WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)`
  - "지난달": `WHERE event_date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH), MONTH) AND LAST_DAY(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH))`
- **Ambiguity Prevention**: ALWAYS use table aliases (e.g. `t1.code`, `t2.destination`) when joining tables. Columns `code` and `destination` exist in multiple tables execution will fail if not qualified.
- **Data Quality**: When querying risk scores (`risk_score`) or damage rates, ALWAYS filter out zero or NULL values (e.g., `WHERE risk_score > 0`) to avoid meaningless results.
- **Uniqueness**: CRITICAL! When ranking items (e.g. 'Top 5'), YOU MUST use `DISTINCT code` or `GROUP BY code`. Duplicate rows may exist in the source.
- **Metric Definitions**:
  - "출고 건수" (Departed Shipments): Shipments started in period. Query `mart_logistics_master`.
    -> `SELECT COUNT(DISTINCT code) FROM mart_logistics_master WHERE departure_date BETWEEN 'START' AND 'END'`
   - "운송 건수" (Active/Total Shipments): Shipments active during the period. Includes those generated before but still in transit or arrived during period.
     -> CRITICAL: DO NOT use `departure_date BETWEEN`.
     -> Correct Logic: `departure_date <= 'END' AND (arrival_date >= 'START' OR arrival_date IS NULL)`
     -> Correct Logic: `departure_date <= 'END' AND (arrival_date >= 'START' OR arrival_date IS NULL)`
     -> Query: `SELECT COUNT(DISTINCT code) FROM mart_logistics_master WHERE departure_date <= 'END' AND (arrival_date >= 'START' OR arrival_date IS NULL)`
   - "일탈률" (Deviation Rate/Excursion Rate):
     -> If Aggregated (Daily/Monthly): `SAFE_DIVIDE(COUNTIF(risk_level IN ('High', 'Critical')), COUNT(*))` in Master.
     -> If by Shipment/Code ("관리번호별 일탈률"): Calculate Sensor Log Excursion Rate.
        Query: `SELECT code, SAFE_DIVIDE(COUNTIF(shock_g >= 5 OR temperature < 2 OR temperature > 8), COUNT(*)) as excursion_rate FROM mart_sensor_detail GROUP BY code`

Code Mapping Guide (Fuzzy Matching & Entity Resolution):
- Shanghai, Sanghai, Sanghi, Shanhai, 상해, 상하이, SH -> 'CNSHG' (or destination LIKE '%Shanghai%')
- Osaka, Osaca, Osk, 오사카, 오사카항 -> 'JPOSA'
- Rizhao, Rizo, 일조, 리자오 -> 'CNRZH'
- Lianyungang, Lianyun, 연운항 -> 'CNLYG'
- Ningbo, Ningpo, 닝보 -> 'CNNBG'
- Hochiminh, HCMC, VN SGN, 호치민 -> 'VNSGN'
- Haiphong, VN HPH, 하이퐁 -> 'VNHPH'
- Incheon, ICN, 인천 -> 'KRICN'
- Busan, Pusan, 부산 -> 'KRPUS'
- "중국", "China", "CN" -> destination_country = 'China' OR destination LIKE 'CN%'
- "베트남", "Vietnam", "VN" -> destination_country = 'Vietnam' OR destination LIKE 'VN%'
- "일본", "Japan", "JP" -> destination_country = 'Japan' OR destination LIKE 'JP%'
- "미국", "USA", "US" -> destination_country = 'USA' OR destination LIKE 'US%'
- "배송 건수", "배송량" -> Same as "출고 건수" (Departed Shipments)
- "물동량" -> Can be "출고 건수" or "운송 건수" depending on context, default to "출고 건수".
- "운송경로", "경로" -> Use `receive_name` column.
- "운송구간", "구간" -> Use `location_fin_corrected` column in `mart_sensor_detail`.

Example SQLs (Few-shot Learning):
1. "🛳️ 해상 운송 중 5G 이상 충격 발생 비율" (Ratio Calculation)
SELECT
    t2.transport_mode,
    COUNTIF(t1.shock_g >= 5) as high_shock_count,
    COUNT(*) as total_sensor_readings,
    SAFE_DIVIDE(COUNTIF(t1.shock_g >= 5), COUNT(*)) as high_shock_ratio
    SAFE_DIVIDE(COUNTIF(t1.shock_g >= 5), COUNT(*)) as high_shock_ratio
FROM `willog-prod-data-gold.rag.mart_sensor_detail` t1
JOIN `willog-prod-data-gold.rag.mart_logistics_master` t2 ON t1.code = t2.code
WHERE t2.transport_mode LIKE 'ocean%' -- Use LIKE for safety or 'ocean'
GROUP BY 1

WHERE t2.transport_mode LIKE 'ocean%' -- Use LIKE for safety or 'ocean'
GROUP BY 1

2. "운송경로 별 도착지 흐름" (Sankey Chart + Active Shipments)
-- Flow Analysis + "운송 건수" (Active) logic
SELECT
    t1.receive_name as source_node,
    t1.destination as target_node,
    COUNT(DISTINCT t1.code) as flow_count
FROM `willog-prod-data-gold.rag.mart_logistics_master` t1
WHERE 
    t1.departure_date <= '2025-12-07' 
    AND (t1.arrival_date >= '2025-12-01' OR t1.arrival_date IS NULL)
GROUP BY 1, 2
ORDER BY 3 DESC

3. "베트남행 화물 중 습도 이탈 구간" (Route/Location Analysis)
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

5. "⚠️ 누적 피로도 Top 5 운송 건" (Ranking with DISTINCT)
SELECT DISTINCT
    code,
    cumulative_shock_index
FROM `willog-prod-data-gold.rag.mart_logistics_master`
WHERE cumulative_shock_index IS NOT NULL
ORDER BY cumulative_shock_index DESC
LIMIT 5

6. "이번 달 운송 건수 및 출고 건수 비교" (Active vs Departed)
SELECT
    COUNT(DISTINCT CASE WHEN t1.departure_date BETWEEN '2025-11-01' AND '2025-11-30' THEN t1.code END) as departed_count,
    COUNT(DISTINCT CASE WHEN t1.departure_date <= '2025-11-30' AND (t1.arrival_date >= '2025-11-01' OR t1.arrival_date IS NULL) THEN t1.code END) as active_transport_count
FROM `willog-prod-data-gold.rag.mart_logistics_master` t1
WHERE t1.departure_date <= '2025-11-30'

7. "도착지별 운송 건수 비중 추이" (Daily Active Ratio Trend)
-- Use mart_sensor_detail for DAILY active status. Window function calculates daily share.
SELECT
    event_date,
    destination,
    COUNT(DISTINCT code) as active_count,
    SAFE_DIVIDE(COUNT(DISTINCT code), SUM(COUNT(DISTINCT code)) OVER (PARTITION BY event_date)) * 100 as share_percentage
FROM `willog-prod-data-gold.rag.mart_sensor_detail`
WHERE event_date BETWEEN '2025-11-01' AND '2025-11-30'
GROUP BY 1, 2
ORDER BY 1, 2

8. "운송 경로 흐름 분석" (Sankey Flow Chart)
-- To trigger Sankey visualization, ALIAS columns as `source_node` and `target_node`.
SELECT
    'Korea' as source_node,
    destination as target_node,
    COUNT(DISTINCT code) as flow_count
FROM `willog-prod-data-gold.rag.mart_sensor_detail`
WHERE event_date BETWEEN '2025-11-01' AND '2025-11-30'
GROUP BY 1, 2
ORDER BY 3 DESC

**Failure Handling (Clarification)**:
- If DATE RANGE is missing for trend queries ("추이 알려줘"), ask: `CLARIFICATION_NEEDED: 언제부터 언제까지의 데이터를 조회할까요?`
- If METRIC is unclear ("물동량 알려줘"), ask: `CLARIFICATION_NEEDED: '출고 건수'(출발 기준)를 원하시나요, 아니면 '운송 건수'(운송 중 포함)를 원하시나요?`
- For Flow/Connection queries ("~별 ~", "흐름", "연결"), ALWAYS return `source_node` and `target_node` columns to show Sankey Chart.
- For Ratio Trend queries ("비중 추이", "점유율 추이"), ALWAYS calculate `SAFE_DIVIDE(..., SUM(...) OVER(PARTITION BY date)) * 100 AS share_percentage` to trigger Stacked Bar Chart.


Previous Conversation Context:
{chat_history}

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

If the result is empty or says "(empty)", say "해당 조건에 맞는 데이터가 없습니다."
Otherwise, summarize the key findings from the result.
Do NOT say there is no data if values are present.

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
    
    def process_query(self, question: str, chat_history: list = None) -> Dict[str, Any]:
        from datetime import date
        current_date = date.today().isoformat()
        
        # Format history logic
        history_str = ""
        if chat_history:
            recent_history = chat_history[-6:] # Context window 6
            for msg in recent_history:
                role = "User" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")
                history_str += f"{role}: {content}\n"

        # 1. Generate SQL
        generated_sql = self.chain.invoke({
            "question": question, 
            "current_date": current_date,
            "chat_history": history_str
        })
        
        print(f"DEBUG: Generated SQL for '{question}': [{generated_sql}]") # Debug log
        
        clean_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
        
        if "CLARIFICATION_NEEDED:" in clean_sql:
            return {
                "question": question,
                "generated_sql": "",
                "result": None,
                "natural_response": clean_sql.replace("CLARIFICATION_NEEDED:", "").strip(),
                "error": None
            }

        if not clean_sql:
            return {
                "question": question,
                "generated_sql": "",
                "result": None,
                "natural_response": "질문을 이해하는데 어려움이 있습니다. 조금 더 구체적으로(기간, 조건 등) 말씀해 주실 수 있나요?",
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
                print(f"DEBUG: Synthesis Input Result:\n{result_str}")
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
