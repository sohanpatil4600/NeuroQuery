import time
import functools
import json
from app.monitoring.collector import collector

def trace_agent(node_name: str):
    """
    Decorator to trace LangGraph agent nodes.
    Captures latency, success/failure, and metadata for the monitoring Hub.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(state: dict, *args, **kwargs):
            import sys
            # Ensure request_id exists, fallback to 'anonymous'
            request_id = state.get("request_id", "anonymous")
            start_t = time.time()
            
            print(f"[TRACING] Entering {node_name} for {request_id}...")
            sys.stdout.flush()

            try:
                # Execute the agent logic
                new_state = func(state, *args, **kwargs)
                status = "success"
                error = None
            except Exception as e:
                status = "error"
                error = str(e)
                new_state = state
                print(f"[TRACING] Exception in {node_name}: {e}")
                sys.stdout.flush()
                # Re-raise to let LangGraph handle/retry the error
                raise e

            end_t = time.time()
            
            # 1. Extract Metadata based on the node
            metadata = {}
            if node_name == "metadata":
                metadata["corrected"] = new_state.get("corrected_question")
                metadata["tables"] = new_state.get("metadata", {}).get("tables")
            elif node_name == "sql":
                metadata["generated_sql"] = new_state.get("sql")
            elif node_name == "execute":
                if new_state.get("error"):
                    metadata["db_error"] = new_state.get("error")
                metadata["retry_count"] = new_state.get("retry_count")
            elif node_name == "bi":
                metadata["interpreted"] = True
                
            # 2. Extract Token Usage
            tokens = new_state.get("last_token_usage", {"input": 0, "output": 0})
            
            # 3. Log to Collector
            try:
                print(f"[TRACING] Saving {node_name} trace...")
                sys.stdout.flush()
                collector.log_agent_step(
                    request_id=request_id,
                    node_name=node_name,
                    start_time=start_t,
                    end_time=end_t,
                    status=status,
                    tokens=tokens,
                    error=error,
                    metadata=metadata
                )
            except Exception as le:
                print(f"[TRACING ERROR] Logging failed: {le}")
                sys.stdout.flush()

            print(f"[TRACING] Exiting {node_name} ({end_t - start_t:.2f}s)")
            sys.stdout.flush()
            return new_state
        return wrapper
    return decorator
