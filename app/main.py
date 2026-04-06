from app.utils.logger_utils import silence_ai_noise
silence_ai_noise()

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from app.langgraph.graph import bi_graph
from app.billing.metering import record_usage, check_limit
from app.monitoring.collector import collector
from dotenv import load_dotenv
import os
import uuid
import time
import json

load_dotenv()

app = FastAPI()

@app.post("/ask/stream")
async def ask_stream(payload: dict):
    try:
        # Enforce limit
        check_limit(payload.get("tenant_id", "t1"), "query", 50)

        async def event_generator():
            request_id = str(uuid.uuid4())
            start_t = time.time()
            total_tokens = 0
            success = False
            from_vault = False
            retry_count = 0
            
            # 1. IMMEDIATE HEARTBEAT (Prevents UI hang during model loading)
            yield json.dumps({
                "node": "orchestrator", 
                "status": "started", 
                "request_id": request_id
            }) + "\n"
            
            try:
                full_state = dict(payload)
                full_state["request_id"] = request_id
                
                # Use astream for async support in FastAPI
                async for chunk in bi_graph.astream(full_state):
                    # Filter for node updates
                    for node_name, state_update in chunk.items():
                        # Yield the node name and essential state info
                        if state_update:
                            full_state.update(state_update)
                        
                        print(f"[STREAM] Node {node_name} completed. Updating state...")
                            
                        yield json.dumps({
                            "node": node_name,
                            "status": "completed",
                            "state_update": {
                                "step": node_name,
                                "retry_count": state_update.get("retry_count", 0) if state_update else 0,
                                "from_vault": state_update.get("from_vault", False) if state_update else False
                            }
                        }) + "\n"
                
                print(f"[STREAM] Finished graph for request {request_id}. Logging final metrics...")
                # Final metrics collection
                success = True
                from_vault = full_state.get("from_vault", False)
                retry_count = full_state.get("retry_count", 0)
                # (Tokens would be summed from the collector's agent_traces if needed, 
                # or we can pass them in the state)
                
                collector.log_request_final(
                    request_id=request_id,
                    total_latency=time.time() - start_t,
                    total_tokens=0, # Placeholder for overall sum
                    success=success,
                    from_vault=from_vault,
                    retry_count=retry_count
                )
                
                # Final completion record with FULL response
                record_usage(payload.get("tenant_id", "t1"), "query", 1)
                yield json.dumps({
                    "status": "done",
                    "request_id": request_id, 
                    "full_data": full_state.get("response", full_state)
                }) + "\n"
            except Exception as e:
                yield json.dumps({
                    "status": "error",
                    "error": str(e)
                }) + "\n"

        return StreamingResponse(event_generator(), media_type="application/x-ndjson")
    except Exception as e:
        # If an error happens BEFORE the stream starts (like Quota Exceeded)
        # Send it as a single-line JSON stream so the UI can catch it
        async def error_generator():
            yield json.dumps({"status": "error", "error": str(e)}) + "\n"
        return StreamingResponse(error_generator(), media_type="application/x-ndjson")

@app.post("/ask")
def ask(payload: dict):
    try:
        # Enforce billing hard-limit before spending LLM tokens
        check_limit(payload.get("tenant_id", "t1"), "query", 50)
        
        request_id = str(uuid.uuid4())
        payload["request_id"] = request_id
        start_t = time.time()
        
        result = bi_graph.invoke(payload)
        
        # Log Final Request Record
        collector.log_request_final(
            request_id=request_id,
            total_latency=time.time() - start_t,
            total_tokens=0,
            success=True,
            from_vault=result.get("from_vault", False),
            retry_count=result.get("retry_count", 0)
        )
        
        record_usage(payload.get("tenant_id", "t1"), "query", 1)
        # Add request_id to response for frontend display if needed
        resp = result["response"]
        resp["request_id"] = request_id
        return resp
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

@app.post("/monitoring/reset")
async def clear_monitoring():
    success = collector.reset_all_metrics()
    return {"status": "success" if success else "failed"}

@app.post("/vault/clear")
async def clear_vault_endpoint():
    from app.agents.vault import clear_vault
    success = clear_vault()
    return {"status": "success" if success else "failed"}
