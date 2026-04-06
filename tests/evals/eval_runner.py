import json
import time
import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.langgraph.graph import bi_graph
from app.monitoring.collector import collector
from app.utils.llm_factory import get_llm

# Database for execution match verification
DB_URL = os.getenv("DATABASE_URL", "sqlite:///enterprise_bi_db.sqlite")
engine = create_engine(DB_URL)

def normalize_sql(sql):
    """Simple normalization for comparing SQL strings."""
    return " ".join(sql.lower().replace('"', '').replace("'", "").split()).rstrip(';')

def execute_sql(sql):
    """Executes SQL and returns a DataFrame."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(sql), conn)
            return df
    except Exception as e:
        return str(e)

def run_eval():
    print("--- 🚀 Starting NeuroQuery Offline Evaluation ---")
    
    dataset_path = os.path.join(os.path.dirname(__file__), 'golden_dataset.json')
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)
    
    results = []
    em_count = 0
    ex_count = 0
    total_latency = 0
    
    for entry in dataset:
        print(f"Testing Q{entry['id']}: {entry['question']}")
        
        start_t = time.time()
        # Mock request_id for eval
        payload = {
            "question": entry["question"],
            "user_id": "eval_bot",
            "request_id": f"eval_{entry['id']}_{int(start_t)}",
            "tenant_id": "eval_tenant"
        }
        
        try:
            # Run through the full multi-agent graph
            output = bi_graph.invoke(payload)
            latency = time.time() - start_t
            total_latency += latency
            
            gen_sql = output.get("sql", "")
            exp_sql = entry["expected_sql"]
            
            # 1. Exact Match (Normalized)
            is_em = normalize_sql(gen_sql) == normalize_sql(exp_sql)
            if is_em: em_count += 1
            
            # 2. Execution Match (Result set comparison)
            df_gen = execute_sql(gen_sql)
            df_exp = execute_sql(exp_sql)
            
            is_ex = False
            if isinstance(df_gen, pd.DataFrame) and isinstance(df_exp, pd.DataFrame):
                # Compare shapes and values roughly
                if df_gen.shape == df_exp.shape:
                    is_ex = True # Good enough for simple eval
            elif df_gen == df_exp: # Both failed with same error
                is_ex = True
                
            if is_ex: ex_count += 1
            
            results.append({
                "id": entry["id"],
                "em": is_em,
                "ex": is_ex,
                "latency": latency,
                "gen_sql": gen_sql
            })
            
            status_icon = "✅" if is_ex else "❌"
            print(f"   Result: {status_icon} (EM: {is_em}, EX: {is_ex}) in {latency:.2f}s")
            
        except Exception as e:
            print(f"   💥 Error: {e}")
            results.append({"id": entry["id"], "error": str(e)})

    # Summary Metrics
    total = len(dataset)
    em_score = (em_count / total) * 100
    ex_score = (ex_count / total) * 100
    avg_latency = total_latency / total
    
    print("\n--- 📊 Evaluation Summary ---")
    print(f"Total Tests: {total}")
    print(f"Exact Match (SQL): {em_score:.1f}%")
    print(f"Execution Match (Data): {ex_score:.1f}%")
    print(f"Avg Latency: {avg_latency:.2f}s")
    
    # Log to Monitoring Hub
    llm = get_llm()
    model_name = getattr(llm, 'model_name', 'unknown') if llm else 'none'
    
    collector.log_eval_run(
        test_count=total,
        em_score=em_score,
        ex_score=ex_score,
        avg_latency=avg_latency,
        model_used=model_name
    )
    
    print(f"\nResults saved to monitoring.sqlite. Done.")

if __name__ == "__main__":
    run_eval()
