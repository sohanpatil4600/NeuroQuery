import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.logger_utils import silence_ai_noise
silence_ai_noise()

import sqlite3
from app.langgraph.graph import bi_graph
from app.agents.vault import VAULT_DB_PATH
import time

def test_dynamic_learning():
    print("\n--- Testing Dynamic Learning Vault ---")
    
    # 1. Very unique question to avoid semantic hits from the 24 pre-seeded questions
    timestamp = int(time.time())
    new_question = f"List all bin numbers in WH_North with storage cost > 4.5 in 2025? (ID: {timestamp})"
    
    user_id = f"test_user_vault_{timestamp}"
    
    # helper for clean state
    def get_state(q=new_question):
        return {
            "question": q,
            "user_id": user_id,
            "history": [],
            "retry_count": 0,
            "from_vault": False 
        }

    # --- RUN 1: Should go through LLM and be CACHED ---
    print("\n[RUN 1] Processing NEW question (LLM required)...")
    res1 = bi_graph.invoke(get_state(new_question))
    
    if res1.get("from_vault"):
        print("❌ FAIL: Question was unexpectedly found in vault on first run.")
    else:
        print("✅ SUCCESS: Question was processed by SQL Agent (LLM).")
        
    # Verify it's in the DB now
    conn = sqlite3.connect(VAULT_DB_PATH)
    row = conn.execute("SELECT id FROM vault WHERE question = ?", (new_question,)).fetchone()
    conn.close()
    
    if row:
        print(f"✅ SUCCESS: New query cached in DB.")
    else:
        print("❌ FAIL: Query was NOT cached in the database.")

    # --- RUN 2: Should be a VAULT HIT ---
    print("\n[RUN 2] Processing identical question (Should be VAULT HIT)...")
    res2 = bi_graph.invoke(get_state(new_question))
    
    if res2.get("from_vault"):
        print("✅ SUCCESS: Question was retrieved from the Dynamic Vault!")
    else:
        print("❌ FAIL: Question was processed by LLM again (Cache missed).")

    # --- RUN 3: Semantic Match ---
    # We use the base question without the ID to test semantic similarity
    semantic_question = f"marketing department total spend 2026 (ID: {timestamp})"
    print(f"\n[RUN 3] Processing semantic variation: '{semantic_question}'...")
    res3 = bi_graph.invoke(get_state(semantic_question))
    
    if res3.get("from_vault"):
        print("✅ SUCCESS: Semantic variation was matched in the Dynamic Vault!")
    else:
        print("❌ FAIL: Semantic match missed.")

if __name__ == "__main__":
    test_dynamic_learning()
