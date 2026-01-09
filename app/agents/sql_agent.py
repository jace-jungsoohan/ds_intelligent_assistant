
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
- `willog-prod-data-gold.rag.view_transport_stats`: Transport volume data
  Columns: date (DATE), destination (STRING), product (STRING), transport_mode (STRING), transport_path (STRING), total_volume (INT64), transport_count (INT64), issue_count (INT64)

- `willog-prod-data-gold.rag.view_issue_stats`: Issue/shock statistics
  Columns: transport_mode (STRING), package_type (STRING), destination (STRING), path_segment (STRING), deviation_rate_5g (FLOAT64), deviation_rate_10g (FLOAT64), cumulative_shock (FLOAT64), shock_count (INT64)

- `willog-prod-data-gold.rag.view_sensor_stats`: Sensor data (temperature, humidity)
  Columns: date (DATE), transport_mode (STRING), destination (STRING), avg_temp (FLOAT64), min_temp (FLOAT64), max_temp (FLOAT64), avg_humidity (FLOAT64), shock_alert_count (INT64)

Rules:
- ALWAYS use fully qualified table names with backticks: `willog-prod-data-gold.rag.table_name`
- Respond ONLY with the SQL query. Do not wrap it in markdown code blocks.
- Current Date: {current_date}

Code Mapping Guide (Interpret location names as follows):
- Shanghai, Sanghai, 상해, 상하이 -> 'CNSHG'
- Osaka, 오사카 -> 'JPOSA'
- Rizhao, 일조, 리자오 -> 'CNRZH'
- Lianyungang, 연운항 -> 'CNLYG'
- Ningbo, 닝보 -> 'CNNBG'
- Vietnam, 베트남 -> (No specific code, search for destination like '%VN%' or strictly match if code known)

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
