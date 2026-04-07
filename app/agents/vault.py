from app.utils.logger_utils import silence_ai_noise
silence_ai_noise()

import sqlite3
import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
import os
import logging

# Database Path
VAULT_DB_PATH = "persistent_vault.sqlite"

# Lazy load Embedder to avoid blocking startup
embedder = None
vault_keys = []
vault_data = {} # {question: {sql, tables}}
vault_embeddings = None

def init_db():
    """Ensure the persistent vault table exists."""
    conn = sqlite3.connect(VAULT_DB_PATH)
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()

def init_vault(force=False):
    """Load all persistent queries from DB and embed them for semantic search."""
    global embedder, vault_keys, vault_data, vault_embeddings
    
    init_db()
    
    # Only re-initialize if needed or forced
    if embedder is not None and not force:
        return

    try:
        print("[VAULT] Syncing Persistent Vault with Semantic Cache...")
        
        # Load from DB
        conn = sqlite3.connect(VAULT_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT question, sql_query, tables_used FROM vault")
        rows = cursor.fetchall()
        conn.close()
        
        vault_keys = [r[0] for r in rows]
        vault_data = {r[0]: {"sql": r[1], "tables": r[2].split(",")} for r in rows}
        
        if not vault_keys:
            print("[VAULT] Note: Persistent vault is currently empty.")
            return

        if embedder is None:
            embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            
        print(f"[VAULT] Embedding {len(vault_keys)} persistent queries in-memory...")
        vault_embeddings = embedder.encode(vault_keys, convert_to_tensor=True, show_progress_bar=False)
        
    except Exception as e:
        print(f"[VAULT] Critical Error during init: {e}")
        embedder = "FAILED"

def add_to_vault(question, sql, tables, is_verified=True):
    """Store a successful new query pair in the persistent vault."""
    try:
        init_db()
        conn = sqlite3.connect(VAULT_DB_PATH)
        cursor = conn.cursor()
        
        # Check if already exists to avoid duplication
        cursor.execute("SELECT id FROM vault WHERE question = ?", (question,))
        if cursor.fetchone():
            conn.close()
            return False
            
        cursor.execute(
            "INSERT INTO vault (question, sql_query, tables_used, is_verified) VALUES (?, ?, ?, ?)",
            (question, sql, ",".join(tables), 1 if is_verified else 0)
        )
        conn.commit()
        conn.close()
        
        # Refresh in-memory cache to include the new entry
        init_vault(force=True)
        print(f"[VAULT] New query successfully cached and embedded: '{question[:50]}...'")
        return True
    except Exception as e:
        print(f"[VAULT] Failed to add to vault: {e}")
        return False

def clear_vault():
    """Wipe the entire persistent vault and reset the cache."""
    try:
        conn = sqlite3.connect(VAULT_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vault")
        conn.commit()
        conn.close()
        # Reset memory-based caches
        global vault_keys, vault_data, vault_embeddings
        vault_keys = []
        vault_data = {}
        vault_embeddings = None
        print("[VAULT] Persistent vault cleared and cache reset.")
        return True
    except Exception as e:
        print(f"[VAULT] Failed to clear: {e}")
        return False

def get_vault_entry(question):
    """Retrieve a verified query pair using exact or semantic matching."""
    q = question.strip().lower().rstrip('.')
    
    init_vault()
    if not vault_keys:
        return None
        
    # 1. Exact Match (Fast)
    for k in vault_keys:
        if k.strip().lower().rstrip('.') == q:
            print(f"[VAULT] Exact match found in persistent storage!")
            # Update hit count
            _update_hit_count(k)
            return vault_data[k]
            
    # 2. Semantic Match
    if embedder == "FAILED":
        return None
        
    try:
        q_emb = embedder.encode(question, convert_to_tensor=True, show_progress_bar=False)
        cos_scores = F.cosine_similarity(q_emb.unsqueeze(0), vault_embeddings)
        
        best_score_idx = torch.argmax(cos_scores).item()
        best_score = cos_scores[best_score_idx].item()
        
        print(f"[VAULT] Top semantic score: {best_score:.2f}")
        
        if best_score > 0.65:
            matched_key = vault_keys[best_score_idx]
            print(f"[VAULT] Semantic match found (Score: {best_score:.2f}): '{matched_key}'")
            _update_hit_count(matched_key)
            return vault_data[matched_key]
    except Exception as e:
        print(f"[VAULT] Runtime Error: {e}")
        
    return None

def _update_hit_count(question):
    """Increment the usage count for a vault entry."""
    try:
        conn = sqlite3.connect(VAULT_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE vault SET hit_count = hit_count + 1 WHERE question = ?", (question,))
        conn.commit()
        conn.close()
    except:
        pass

# Legacy VAULT dictionary has been moved to archive/seed_vault.py or can be recreated from persistent_vault.sqlite.
