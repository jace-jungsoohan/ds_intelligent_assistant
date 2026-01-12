
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_vertexai import ChatVertexAI
from app.core.config import settings








# Initialize Vertex AI Model
try:
    llm = ChatVertexAI(
        model_name="gemini-2.5-flash",
        project=settings.PROJECT_ID,
        location=settings.LOCATION,
        temperature=0,
    )
except Exception as e:
    print(f"Warning: Router LLM init failed: {e}")
    llm = None

# Router Prompt (omitted for brevity, assume existing)
template_router = """
You are a routing assistant for Willog's Intelligent Assistant. Your task is to analyze the user's question and route it to the most appropriate agent.

━━━━━━━━━━━━━━━━━━━━ Agents & Selection Criteria ━━━━━━━━━━━━━━━━━━━━

1. SQL_AGENT
목적: 데이터베이스의 수치, 통계, 실시간 상태 조회가 필요할 때
판단 기준:
- 구체적인 숫자, 건수, 평균, 비율, 순위, 트렌드를 묻는 경우
- 특정 ID(송장번호, 차량번호), 노선, 출발/도착지, 센서값이 포함된 경우
- 시간 표현(어제, 지난달, 1분기 등)이 들어간 구체적 데이터 요청
예시: "어제 베트남행 배송 몇 건이야?", "온도 일탈이 가장 많은 노선 알려줘", "A123 적정 온도 유지됐어?", "지난주 평균 습도 보여줘"

2. RETRIEVAL_AGENT
목적: 문서, 가이드라인, 규정, 정의 등 텍스트 기반 정보 설명이 필요할 때
판단 기준:
- "방법", "기준", "정의", "이유", "매뉴얼"에 대해 묻는 경우
- 수치 자체가 아니라, 그 수치가 계산되는 로직이나 정책을 묻는 경우
- 원인 분석이나 대처 요령 등 정성적인 답변이 필요한 경우
예시: "동절기 운송 지침이 뭐야?", "온도 일탈 기준이 어떻게 돼?", "일탈률은 어떻게 계산해?", "충격 이벤트 발생 시 대처법 알려줘"

3. GENERAL_AGENT
목적: 일상적인 대화, 서비스 일반 안내, 시스템 기능 문의
판단 기준:
- 인사, 감사, 작별 인사
- "너는 누구니?", "뭐 할 수 있어?"와 같은 챗봇 기능 문의
- 물류 일반 상식이나 Willog 서비스 자체에 대한 추상적 질문
예시: "안녕", "고마워", "윌로그 서비스에 대해 소개해줘", "물류가 뭐야?"

━━━━━━━━━━━━━━━━━━━━ Priority Rules (우선순위) ━━━━━━━━━━━━━━━━━━━━

수치 vs 로직: "지난주 일탈률(데이터)과 그 기준(로직)을 알려줘"처럼 복합적인 경우, SQL_AGENT를 우선합니다. (데이터 확인이 우선순위가 높음)
원인 파악: "왜 온도가 높아?"라고 물었을 때, 실제 온도 데이터를 확인해야 하면 SQL_AGENT, 일반적인 원인(여름철 특성 등)을 묻는 것이면 RETRIEVAL_AGENT로 보냅니다. 모호하면 SQL_AGENT로 분류합니다.
고유 명사: 특정 ID, 노선명, 지점명이 언급되면 99% 확률로 SQL_AGENT입니다.

━━━━━━━━━━━━━━━━━━━━ Output Rules (Strictly Enforced) ━━━━━━━━━━━━━━━━━━━━

Output MUST be exactly one of the following strings: SQL_AGENT RETRIEVAL_AGENT GENERAL_AGENT
DO NOT include any other text, explanation, punctuation, or markdown.
DO NOT translate the agent names.
DO NOT respond in Korean (ONLY output the English agent name).

Question: {question}
Agent:
"""

prompt_router = ChatPromptTemplate.from_template(template_router)

# Fallback for classification if LLM is unavailable
# Fallback for classification if LLM is unavailable
def mock_router(question: str):
    keywords_general = ["hi", "hello", "help", "who are you", "what can you do", "안녕", "반가워", "도와줘", "누구", "기능", "소개"]
    if any(k in question.lower() for k in keywords_general):
        return "GENERAL_AGENT"

    keywords_sql = ["count", "amount", "volume", "rate", "temperature", "humidity", "shock", "stats", "data", "how many", "percentage", "average", "통계", "수량", "건수", "파손율", "온도", "습도", "충격"]
    if any(k in question.lower() for k in keywords_sql):
        return "SQL_AGENT"
        
    return "RETRIEVAL_AGENT"

if llm:
    router_chain = prompt_router | llm | StrOutputParser()
else:
    # Use fallback mock
    class MockRouterChain:
        def invoke(self, input_dict):
            return mock_router(input_dict["question"])
    router_chain = MockRouterChain()

def route_query(question: str) -> str:
    """Classifies the query and returns 'SQL_AGENT', 'RETRIEVAL_AGENT', or 'GENERAL_AGENT'."""
    try:
        decision = router_chain.invoke({"question": question}).strip()
        # Clean up potential markdown formatting
        decision = decision.replace("`", "").replace("csv", "").strip()
        
        valid_agents = ["SQL_AGENT", "RETRIEVAL_AGENT", "GENERAL_AGENT"]
        if decision not in valid_agents:
             # If LLM hallucinates, try fallback keyword matching
             print(f"Router Warning: Invalid agent '{decision}', falling back to keyword search.")
             return mock_router(question)
             
        return decision
        return decision
    except Exception as e:
        print(f"Router Error: {e}")
        return "SQL_AGENT"
