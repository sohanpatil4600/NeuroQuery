from sqlalchemy import create_engine, text
import os

# Use Environment Variable for DB URL if available (e.g., Postgres on Vercel/Streamlit Cloud)
# Fallback to local SQLite file for demos/local runs
DB_URL = os.getenv("DATABASE_URL", "sqlite:///enterprise_bi_db.sqlite")

engine = create_engine(DB_URL)

def run(state):
    with engine.connect() as conn:
        res = conn.execute(text(state["sql"]))
        # Convert to list of dicts for easier downstream processing
        state["result"] = [dict(row._mapping) for row in res]
    return state
