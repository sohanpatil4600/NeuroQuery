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

# Fallback Legacy Dictionary (For seeding and initial dev)
VAULT = {
    "Compare allocated budget vs actual spend by department for all quarters of 2025.": {
        "sql": "SELECT department, year, quarter, SUM(allocated_budget) as total_budget, SUM(actual_spend) as total_actual FROM operating_budget WHERE year = 2025 GROUP BY department, quarter",
        "tables": ["operating_budget"]
    },
    "Which departments have the highest total expenses across 2024 and 2025?": {
        "sql": "SELECT department_id, SUM(amount) as total_expenses FROM expenses WHERE date BETWEEN '2024-01-01' AND '2025-12-31' GROUP BY department_id ORDER BY total_expenses DESC",
        "tables": ["expenses"]
    },
    "What is the total projected revenue for each month in 2026 based on current sales?": {
        "sql": "SELECT strftime('%Y-%m', date) as month, SUM(revenue) * 1.15 as projected_revenue FROM sales WHERE date LIKE '2026%' GROUP BY month ORDER BY month",
        "tables": ["sales"]
    },
    "Show me departments where actual spend exceeded the budget by more than 10%.": {
        "sql": "SELECT department, year, quarter, allocated_budget, actual_spend, ((actual_spend - allocated_budget)/allocated_budget)*100 as variance_pct FROM operating_budget WHERE actual_spend > (allocated_budget * 1.10)",
        "tables": ["operating_budget"]
    },
    "Break down total operating expenses by category for the last 12 months.": {
        "sql": "SELECT category, SUM(amount) as total_amount FROM expenses WHERE date >= date('now', '-12 months') GROUP BY category ORDER BY total_amount DESC",
        "tables": ["expenses"]
    },
    "Calculate regional ROI by comparing marketing spend vs sales revenue for each region.": {
        "sql": "SELECT m.region, (SUM(s.revenue) / SUM(m.spend)) as regional_ROI, SUM(m.spend) as total_marketing_spend, SUM(s.revenue) as total_sales_revenue FROM marketing m JOIN sales s ON m.region = s.region WHERE m.date BETWEEN '2024-01-01' AND '2025-12-31' AND s.date BETWEEN '2024-01-01' AND '2025-12-31' GROUP BY m.region",
        "tables": ["marketing", "sales"]
    },
    "What are the top 3 reasons for customer churn in the last year?": {
        "sql": "SELECT primary_reason, COUNT(*) as churn_count FROM churn_analysis WHERE churn_date >= date('now', '-1 year') GROUP BY primary_reason ORDER BY churn_count DESC LIMIT 3",
        "tables": ["churn_analysis"]
    },
    "Show me the count of active vs canceled subscriptions across all plans.": {
        "sql": "SELECT plan_name, status, COUNT(*) as count FROM subscriptions GROUP BY plan_name, status",
        "tables": ["subscriptions"]
    },
    "Which loyalty tier (Gold/Silver/Bronze) has the highest total lifetime spend?": {
        "sql": "SELECT loyalty_tier, SUM(total_spend) as lifetime_spend FROM customers GROUP BY loyalty_tier ORDER BY lifetime_spend DESC",
        "tables": ["customers"]
    },
    "Show a monthly trend of new customer signups from 2023 to 2025.": {
        "sql": "SELECT strftime('%Y-%m', signup_date) as month, COUNT(*) as signups FROM customers WHERE signup_date BETWEEN '2023-01-01' AND '2025-12-31' GROUP BY month ORDER BY month",
        "tables": ["customers"]
    },
    "Compare the total spend of customers acquired through Google Ads vs Referrals.": {
        "sql": "SELECT acquisition_channel, SUM(total_spend) as total_revenue FROM customers WHERE acquisition_channel IN ('GAds', 'Referral') GROUP BY acquisition_channel",
        "tables": ["customers"]
    },
    "Show me the MRR (Monthly Recurring Revenue) share percentage of SaaS Pro vs Elite.": {
        "sql": "SELECT plan_name, SUM(monthly_price) as MRR FROM subscriptions WHERE status = 'Active' AND plan_name IN ('SaaS Pro', 'SaaS Elite') GROUP BY plan_name",
        "tables": ["subscriptions"]
    },
    "Show me the correlation between website sessions and marketing conversions for 2024.": {
        "sql": "SELECT strftime('%Y-%m', date) as month, SUM(sessions) as sessions, SUM(conversions) as conversions FROM website_traffic WHERE date LIKE '2024%' GROUP BY month",
        "tables": ["website_traffic"]
    },
    "Compare our SaaS Pro price against the average competitor market price.": {
        "sql": "SELECT 'SaaS Pro' as product, 99.99 as our_price, AVG(market_price) as market_avg FROM competitor_metrics WHERE product_name = 'Standard Plan'",
        "tables": ["competitor_metrics", "products"]
    },
    "Identify the marketing campaign with the single highest ROI ever recorded.": {
        "sql": "SELECT name, roi, spend, conversions FROM marketing ORDER BY roi DESC",
        "tables": ["marketing"]
    },
    "Compare the conversion rates of Mobile traffic vs Desktop traffic.": {
        "sql": "SELECT device_type, AVG(conversion_rate) as avg_conv_rate FROM website_traffic GROUP BY device_type",
        "tables": ["website_traffic"]
    },
    "Which marketing channel (FB, GAds, LI) has the lowest cost-per-conversion?": {
        "sql": "SELECT channel, SUM(spend)/SUM(conversions) as cost_per_conv FROM marketing GROUP BY channel ORDER BY cost_per_conv ASC",
        "tables": ["marketing"]
    },
    "Analyze the impact of product reviews on regional sales growth.": {
        "sql": "SELECT s.region, AVG(pr.sentiment_score) as avg_sentiment, SUM(s.revenue) as revenue FROM product_reviews pr JOIN products p ON pr.product_id = p.product_id JOIN sales s ON p.name = s.product GROUP BY s.region",
        "tables": ["product_reviews", "sales", "products"]
    },
    "Show me the average resolution time for High Priority tickets by support agent.": {
        "sql": "SELECT agent_name, AVG(resolution_time_hrs) as avg_hours FROM support_tickets WHERE priority = 'High' GROUP BY agent_name",
        "tables": ["support_tickets"]
    },
    "List all products where the current quantity on hand is below the reorder point.": {
        "sql": "SELECT p.name, i.warehouse_location, i.quantity_on_hand, i.reorder_point FROM inventory i JOIN products p ON i.product_id = p.product_id WHERE i.quantity_on_hand < i.reorder_point",
        "tables": ["inventory", "products"]
    },
    "Rank our top 5 Sales Reps by their Actual Sales vs Quota performance.": {
        "sql": "SELECT name, actual_sales, quota, (actual_sales/quota)*100 as pct_attainment FROM employee_performance WHERE role = 'Sales Rep' ORDER BY pct_attainment DESC LIMIT 5",
        "tables": ["employee_performance"]
    },
    "Identify all non-tax-deductible expenses greater than $5000 in the IT department.": {
        "sql": "SELECT vendor_name, amount FROM expenses WHERE tax_deductible = 0 AND amount > 5000 AND department_id = 'IT' ORDER BY amount DESC",
        "tables": ["expenses"]
    },
    "Show the distribution of inventory quantity across all warehouse locations.": {
        "sql": "SELECT warehouse_location, SUM(quantity_on_hand) as total_inventory FROM inventory GROUP BY warehouse_location",
        "tables": ["inventory"]
    },
    "Calculate the average customer satisfaction score for bug-related tickets.": {
        "sql": "SELECT agent_name, AVG(customer_satisfaction) as avg_score FROM support_tickets WHERE issue_type = 'Bug' GROUP BY agent_name ORDER BY avg_score DESC",
        "tables": ["support_tickets"]
    }
}
