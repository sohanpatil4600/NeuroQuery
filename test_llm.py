import os
import sys
# Add app to path
sys.path.append(os.getcwd())

from app.utils.llm_factory import get_llm
from dotenv import load_dotenv

load_dotenv()

print("--- Testing Default (Groq) ---")
llm = get_llm()
if llm:
    print(f"Resulting LLM: {type(llm).__name__}")

print("\n--- Testing OpenAI Override ---")
os.environ["PREFERRED_LLM"] = "openai"
llm_oa = get_llm()
if llm_oa:
    print(f"Resulting LLM: {type(llm_oa).__name__}")
