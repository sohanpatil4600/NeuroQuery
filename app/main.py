from app.utils.logger_utils import silence_ai_noise
silence_ai_noise()

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from app.langgraph.graph import bi_graph
from app.billing.metering import record_usage, check_limit
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

@app.post("/ask/stream")
async def ask_stream(payload: dict):
    try:
        # Enforce limit
        check_limit(payload.get("tenant_id", "t1"), "query", 50)

        async def event_generator():
            try:
                full_state = dict(payload)
                # Use astream for async support in FastAPI
                async for chunk in bi_graph.astream(payload):
                    # Filter for node updates
                    for node_name, state_update in chunk.items():
                        import json
                        # Yield the node name and essential state info
                        if state_update:
                            full_state.update(state_update)
                            
                        yield json.dumps({
                            "node": node_name,
                            "status": "completed",
                            "state_update": {
                                "step": node_name,
                                "retry_count": state_update.get("retry_count", 0) if state_update else 0,
                                "from_vault": state_update.get("from_vault", False) if state_update else False
                            }
                        }) + "\n"
                
                # Final completion record with FULL response
                record_usage(payload.get("tenant_id", "t1"), "query", 1)
                yield json.dumps({
                    "status": "done",
                    "full_data": full_state.get("response", full_state)
                }) + "\n"
            except Exception as e:
                import json
                yield json.dumps({
                    "status": "error",
                    "error": str(e)
                }) + "\n"

        return StreamingResponse(event_generator(), media_type="application/x-ndjson")
    except Exception as e:
        return {"error": str(e), "status": "failed"}

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

@app.post("/memory/clear")
async def clear_memory(payload: dict):
    from app.memory.mem0_client import clear_long_term_memory
    user_id = payload.get("user_id", "u1")
    success = clear_long_term_memory(user_id=user_id)
    return {"status": "success" if success else "failed"}

@app.post("/vault/clear")
async def clear_vault_endpoint():
    from app.agents.vault import clear_vault
    success = clear_vault()
    return {"status": "success" if success else "failed"}
