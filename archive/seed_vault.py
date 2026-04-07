import sqlite3
import os
import sys

# Add parent dir to path so we can import app.agents.vault
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.vault import VAULT, VAULT_DB_PATH

def seed_vault():
    print(f"Connecting to {VAULT_DB_PATH}...")
    conn = sqlite3.connect(VAULT_DB_PATH)
    cursor = conn.cursor()
    
    # Create table if not exists (though vault.py should handle this)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vault (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT UNIQUE,
            sql_query TEXT,
            tables_used TEXT,
            is_verified BOOLEAN DEFAULT 0,
            hit_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    count = 0
    for question, data in VAULT.items():
        try:
            cursor.execute(
                "INSERT INTO vault (question, sql_query, tables_used, is_verified) VALUES (?, ?, ?, ?)",
                (question, data["sql"], ",".join(data["tables"]), 1)
            )
            count += 1
        except sqlite3.IntegrityError:
            # Already exists
            pass
            
    conn.commit()
    conn.close()
    print(f"Successfully seeded {count} queries into the persistent vault.")

if __name__ == "__main__":
    seed_vault()
