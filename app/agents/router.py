
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
        temperature=0
    )
except Exception as e:
    print(f"Warning: Router LLM init failed: {e}")
    llm = None

# Router Prompt (omitted for brevity, assume existing)
template_router = """
You are a router assistant for Willog's Intelligent Assistant.
Route the user's question to the appropriate agent.

**Agents:**
1. `SQL_AGENT`: For questions about quantifiable data, statistics, transport volumes, deviation rates, shock counts, or sensor data summaries. (e.g., "How many shipments to Vietnam?", "What was the average temperature last week?", "Show me the deviation rate.")
2. `RETRIEVAL_AGENT`: For questions about reports, policies, guidelines, document contents, or qualitative analysis found in reports. (e.g., "What is the policy for winter transport?", "Explain the shock measurement criteria.", "Why is the deviation rate calculated this way?")
3. `GENERAL_AGENT`: For greetings, capabilities, general terms, or conversational inputs. (e.g., "Hello", "What can you do?", "What is Willog?", "Explain logisitcs in general")

**Rules:**
- If the question requires database aggregation or statistics, choose `SQL_AGENT`.
- If the question requires reading reporting guidelines or text documents, choose `RETRIEVAL_AGENT`.
- If the question is a greeting or general inquiry about the system, choose `GENERAL_AGENT`.
- Output ONLY the agent name: `SQL_AGENT`, `RETRIEVAL_AGENT`, or `GENERAL_AGENT`.

Question: {question}
Agent:
"""

prompt_router = ChatPromptTemplate.from_template(template_router)

# Fallback for classification if LLM is unavailable
def mock_router(question: str):
    keywords_sql = ["count", "amount", "volume", "rate", "temperature", "humidity", "shock", "stats", "data", "how many", "percentage", "average"]
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
    """Classifies the query and returns 'SQL_AGENT' or 'RETRIEVAL_AGENT'."""
    try:
        decision = router_chain.invoke({"question": question}).strip()
        # Clean up potential markdown formatting
        decision = decision.replace("`", "").replace("csv", "").strip()
        if decision not in ["SQL_AGENT", "RETRIEVAL_AGENT"]:
             return "SQL_AGENT" # Default
        return decision
    except Exception as e:
        print(f"Router Error: {e}")
        return "SQL_AGENT"
