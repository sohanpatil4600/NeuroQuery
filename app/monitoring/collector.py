import sqlite3
import json
import time
from datetime import datetime
from threading import Lock

class MonitoringCollector:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MonitoringCollector, cls).__new__(cls)
                cls._instance._initialize_db()
        return cls._instance

    def _initialize_db(self):
        self.db_path = 'monitoring.sqlite'
        # check_same_thread=False is needed for multi-threaded FastAPI/Uvicorn
        # timeout=30 helps prevent "Database is locked" errors
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
        cursor = conn.cursor()
        
        # --- PRODUCTION HARDENING ---
        # WAL mode allows multiple readers and 1 writer without blocking
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('PRAGMA synchronous=NORMAL;')
        
        # Table for individual agent execution traces
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_traces (
                trace_id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT,
                node_name TEXT,
                start_time REAL,
                end_time REAL,
                latency REAL,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                status TEXT,
                error_message TEXT,
                metadata TEXT
            )
        ''')
        
        # Table for overall request metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS request_metrics (
                request_id TEXT PRIMARY KEY,
                timestamp TEXT,
                total_latency REAL,
                total_tokens INTEGER,
                success INTEGER,
                from_vault INTEGER,
                retry_count INTEGER
            )
        ''')
        
        # Table for offline evaluation results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS eval_history (
                eval_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                test_count INTEGER,
                exact_match_score REAL,
                execution_match_score REAL,
                avg_latency REAL,
                model_used TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)

    def reset_all_metrics(self):
        """Destructive action: Wipes all monitoring and evaluation history."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS agent_traces")
            cursor.execute("DROP TABLE IF EXISTS request_metrics")
            cursor.execute("DROP TABLE IF EXISTS eval_history")
            conn.commit()
            conn.close()
            # Re-initialize the schema
            self._initialize_db()
            print("[COLLECTOR] Monitoring data reset successfully.")
            return True
        except Exception as e:
            print(f"[COLLECTOR ERROR] Reset failed: {e}")
            return False

    def log_agent_step(self, request_id, node_name, start_time, end_time, status, tokens=None, error=None, metadata=None):
        latency = end_time - start_time
        tokens = tokens or {"input": 0, "output": 0}
        metadata_json = json.dumps(metadata) if metadata else None
        
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO agent_traces 
            (request_id, node_name, start_time, end_time, latency, input_tokens, output_tokens, status, error_message, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (request_id, node_name, start_time, end_time, latency, tokens.get("input", 0), tokens.get("output", 0), status, error, metadata_json))
        conn.commit()
        conn.close()

    def log_request_final(self, request_id, total_latency, total_tokens, success, from_vault, retry_count):
        conn = self._get_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO request_metrics 
            (request_id, timestamp, total_latency, total_tokens, success, from_vault, retry_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (request_id, timestamp, total_latency, total_tokens, 1 if success else 0, 1 if from_vault else 0, retry_count))
        conn.commit()
        conn.close()

    def log_eval_run(self, test_count, em_score, ex_score, avg_latency, model_used):
        conn = self._get_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO eval_history 
            (timestamp, test_count, exact_match_score, execution_match_score, avg_latency, model_used)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, test_count, em_score, ex_score, avg_latency, model_used))
        conn.commit()
        conn.close()

# Global instance
collector = MonitoringCollector()
