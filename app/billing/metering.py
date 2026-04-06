import sqlite3
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'billing_db.sqlite')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            metric_type TEXT,
            value INTEGER,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            user_id TEXT,
            question TEXT,
            answer TEXT,
            sql_query TEXT,
            metadata_json TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize upon import
init_db()

def record_usage(tenant_id, metric, value):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute(
            'INSERT INTO usage_logs (tenant_id, metric_type, value, timestamp) VALUES (?, ?, ?, ?)',
            (tenant_id, metric, value, now)
        )
        conn.commit()
        conn.close()
        print(f"[BILLING] Recorded {value} {metric} for {tenant_id}")
    except Exception as e:
        print(f"[BILLING ERROR] Unable to record usage: {e}")

def check_limit(tenant_id, metric, limit):
    """
    Checks if the given tenant has exceeded the limit.
    Raises Exception if exceeded.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Ensure fast resolution of aggregate without date bounding for MVP
        cursor.execute(
            'SELECT SUM(value) FROM usage_logs WHERE tenant_id = ? AND metric_type = ?',
            (tenant_id, metric)
        )
        result = cursor.fetchone()[0]
        conn.close()
        
        current_usage = result if result else 0
        if current_usage >= limit:
            raise Exception(f"Quota Exceeded: {tenant_id} has used {current_usage}/{limit} {metric}s.")
        return True
    except Exception as e:
        if "Quota Exceeded" in str(e):
            raise e
        print(f"[BILLING ERROR] check_limit failed: {e}")
        # Allow pass-through if DB fails so we don't block legitimate usage
        return True

def save_conversation(tenant_id, user_id, question, answer, sql_query, metadata_json):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute('''
            INSERT INTO conversations (tenant_id, user_id, question, answer, sql_query, metadata_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (tenant_id, user_id, question, answer, sql_query, metadata_json, now))
        conn.commit()
        conn.close()
        print(f"[CONVERSATION] Saved history for {user_id}")
    except Exception as e:
        print(f"[DB ERROR] save_conversation failed: {e}")

def get_conversation_history(tenant_id, user_id, limit=10):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT question, answer, sql_query, metadata_json, timestamp 
            FROM conversations 
            WHERE tenant_id = ? AND user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (tenant_id, user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for r in rows:
            history.append({
                "question": r[0],
                "answer": r[1],
                "sql": r[2],
                "metadata": r[3],
                "timestamp": r[4]
            })
        return history
    except Exception as e:
        print(f"[DB ERROR] get_conversation_history failed: {e}")
        return []
