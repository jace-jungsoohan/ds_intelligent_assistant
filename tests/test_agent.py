
import sys
import os
try:
    import importlib.metadata
    if not hasattr(importlib.metadata, "packages_distributions"):
        import importlib_metadata
        importlib.metadata.packages_distributions = importlib_metadata.packages_distributions
except ImportError:
    pass

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.sql_agent import agent

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_agent.py 'Your question here'")
        sys.exit(1)
    
    question = sys.argv[1]
    print(f"--- Processing Query: {question} ---")

    
    try:
        # Mocking the chain for environment without credentials
        from unittest.mock import MagicMock
        
        # We replace the actual chain with a mock that returns a sample SQL
        # This allows us to verify the agent's structure/logic works (parsing, execution flow)
        # even if we can't call the real LLM here.
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = """```sql
SELECT 
    destination,
    SUM(total_volume) as total_volume
FROM `willog-prod-data-gold.rag.view_transport_stats`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)
AND destination = 'Vietnam'
GROUP BY destination
```"""
        agent.chain = mock_chain
        
        response = agent.process_query(question)
        print("\n[Generated SQL]")
        print(response["generated_sql"])
        
        if response["error"]:
            print(f"\n[Execution Error (Expected if no creds)]: {response['error']}")
        elif response["result"] is not None:
             print("\n[Result Dataframe]")
             print(response["result"])
        
    except Exception as e:
        print(f"An error occurred: {e}")
