from fastapi import FastAPI
from app.langgraph.graph import bi_graph
from app.billing.metering import record_usage, check_limit
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

@app.post("/ask")
def ask(payload: dict):
    try:
        # Enforce billing hard-limit before spending LLM tokens
        check_limit(payload.get("tenant_id", "t1"), "query", 50)
        
        result = bi_graph.invoke(payload)
        record_usage(payload.get("tenant_id", "t1"), "query", 1)
        return result["response"]
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "status": "failed"}
