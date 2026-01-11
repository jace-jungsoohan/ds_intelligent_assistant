
import sys
import os


# Ensure app is in path (project root)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.agents.router import route_query
from app.agents.sql_agent import agent as sql_agent_instance
from app.agents.retrieval_agent import retrieval_agent as retrieval_agent_instance
from app.agents.general_agent import general_agent as general_agent_instance

class Orchestrator:
    def run(self, question: str, chat_history: list = None):
        print(f"User Query: {question}")
        
        # 1. Route
        target_agent = route_query(question)
        print(f"Selected Agent: {target_agent}")
        
        # 2. Execute
        response = None
        if target_agent == "SQL_AGENT":
            print("--- Invoking SQL Agent ---")
            response = sql_agent_instance.process_query(question, chat_history)
            
            # Use natural language response from synthesis
            if response.get("natural_response"):
                final_answer = response.get("natural_response")
            elif response.get("error"):
                final_answer = f"죄송합니다. 데이터베이스 조회 중 오류가 발생했습니다: {response['error']}"
            else:
                final_answer = f"생성된 SQL:\n{response.get('generated_sql')}"
            
            # Also show the SQL for debugging
            print(f"\n[Generated SQL]\n{response.get('generated_sql')}")
                
        elif target_agent == "RETRIEVAL_AGENT":
            print("--- Invoking Retrieval Agent ---")
            response = retrieval_agent_instance.process_query(question)
            final_answer = response.get("answer")
            
        elif target_agent == "GENERAL_AGENT":
            print("--- Invoking General Agent ---")
            final_answer = general_agent_instance.process_query(question, chat_history)
            
        else:
            final_answer = "Unknown agent selected."

        print("\n[Final Answer]")
        print(final_answer)
        return {
            "text": final_answer,
            "data": response.get("result") if target_agent == "SQL_AGENT" and response and isinstance(response, dict) else None,
            "sql": response.get("generated_sql") if target_agent == "SQL_AGENT" and response and isinstance(response, dict) else None,
            "agent": target_agent
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app/agents/orchestrator.py 'Question'")
        sys.exit(1)
    
    orchestrator = Orchestrator()
    orchestrator.run(sys.argv[1])
