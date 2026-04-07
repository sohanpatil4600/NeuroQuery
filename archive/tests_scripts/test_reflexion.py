import sys
import os

# Add parent dir to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.langgraph.graph import bi_graph
from dotenv import load_dotenv

load_dotenv()

def test_self_healing():
    print("--- Running Self-Healing Verification ---")
    
    # We ask a question that might lead to a typo in the column name if the LLM isn't careful,
    # or we can manually observe the retry logs.
    # To TRULY force a retry, we'd need to mock the SQL agent to fail first, 
    # but let's see if a natural 'tricky' question triggers it.
    
    # Question that will DEFINITELY fail as 'abc_table' doesn't exist
    test_payload = {
        "question": "Show me the value of xyz_column from the table abc_table",
        "tenant_id": "test_tenant",
        "user_id": "test_user",
        "history": []
    }
    
    print(f"Question: {test_payload['question']}")
    
    # Run the graph
    result = bi_graph.invoke(test_payload)
    
    print("\n--- FINAL RESULT ---")
    print(f"Retry Count: {result.get('retry_count', 0)}")
    print(f"Final SQL: {result.get('sql')}")
    
    if result.get('retry_count', 0) > 0:
        print("✅ SUCCESS: Self-healing loop was triggered and handled!")
    else:
        print("ℹ️ NOTE: SQL Agent was smart enough to get it right the first time! To force a retry, we would need to mock a failure.")

    if result.get('error'):
        print(f"❌ FAILED: Still have an error: {result['error']}")
    else:
        print("✅ SUCCESS: Execution was successful.")

if __name__ == "__main__":
    test_self_healing()
