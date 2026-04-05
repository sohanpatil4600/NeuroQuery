from sqlalchemy import create_engine, text
import os

# Use Environment Variable for DB URL if available (e.g., Postgres on Vercel/Streamlit Cloud)
# Fallback to local SQLite file for demos/local runs
DB_URL = os.getenv("DATABASE_URL", "sqlite:///enterprise_bi_db.sqlite")

engine = create_engine(DB_URL)

from sqlalchemy.exc import SQLAlchemyError

def run(state):
    # Initialize error and retry_count if not present
    if "error" not in state:
        state["error"] = ""
    if "retry_count" not in state:
        state["retry_count"] = 0

    try:
        with engine.connect() as conn:
            res = conn.execute(text(state["sql"]))
            # Convert to list of dicts for easier downstream processing
            state["result"] = [dict(row._mapping) for row in res]
            state["error"] = "" # Clear error on success
    except SQLAlchemyError as e:
        # Extract the clear error message for the SQL Agent to fix
        error_msg = str(e.__dict__.get('orig', e))
        print(f"[EXECUTE] Error detected: {error_msg}")
        state["error"] = error_msg
        state["result"] = [] # Reset results on failure
        
    return state
