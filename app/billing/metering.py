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
