import sys
import os

# add parent dir to path so we can import app.agents.vault
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.vault import get_vault_entry

# A highly modified human version of the predefined query:
# "Which loyalty tier (Gold/Silver/Bronze) has the highest total lifetime spend?"
test_question = "Out of all the loyalty tiers, tell me which one practically spent the most total money in their lifetime?"

print(f"Testing semantic cache with input:\n'{test_question}'\n")

print("Initializing Vault Model (simulating first request)...")
result = get_vault_entry(test_question)

if result:
    print("\nSUCCESS! Intercepted by Vault!")
    print(f"SQL: {result['sql']}")
else:
    print("\nFAILED. Vault did not catch it.")
