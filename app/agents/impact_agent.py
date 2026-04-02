import re
from typing import Dict, Any

# --- Configuration ---
# Define sensitive tables and columns
SENSITIVE_TABLES = {"users", "credentials", "passwords", "pii", "financial", "payroll"}
SENSITIVE_COLUMNS = {"ssn", "credit_card", "password", "email", "phone", "address", "dob"}

# Define "destructive" operations
DESTRUCTIVE_KEYWORDS = {"DROP", "DELETE", "TRUNCATE", "UPDATE", "ALTER", "GRANT", "REVOKE"}

# Define "read-only" operations (safe)
READ_ONLY_KEYWORDS = {"SELECT", "DESCRIBE", "SHOW", "PRAGMA"}

# --- Helper Functions ---
def extract_tables(sql: str) -> set:
    """Extract table names from SQL query using regex."""
    tables = set()
    
    # Match FROM clause
    from_match = re.search(r'FROM\s+([a-zA-Z0-9_]+)', sql, re.IGNORECASE)
    if from_match:
        tables.add(from_match.group(1).lower())
    
    # Match JOIN clauses
    join_matches = re.findall(r'JOIN\s+([a-zA-Z0-9_]+)', sql, re.IGNORECASE)
    for table in join_matches:
        tables.add(table.lower())
    
    # Match UPDATE clause
    update_match = re.search(r'UPDATE\s+([a-zA-Z0-9_]+)', sql, re.IGNORECASE)
    if update_match:
        tables.add(update_match.group(1).lower())
    
    # Match INSERT INTO clause
    insert_match = re.search(r'INSERT\s+INTO\s+([a-zA-Z0-9_]+)', sql, re.IGNORECASE)
    if insert_match:
        tables.add(insert_match.group(1).lower())
    
    return tables

def extract_columns(sql: str) -> set:
    """Extract column names from SQL query using regex."""
    columns = set()
    
    # Match SELECT columns (before FROM)
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE)
    if select_match:
        columns_str = select_match.group(1)
        # Split by comma and clean up
        for col in columns_str.split(','):
            col = col.strip()
            # Remove table prefix if present (e.g., "users.id" -> "id")
            col = col.split('.')[-1]
            # Remove quotes if present
            col = col.replace('"', '').replace("'", '').replace('`', '')
            if col and col != '*':
                columns.add(col.lower())
    
    # Match UPDATE columns (in SET clause)
    update_match = re.search(r'SET\s+(.*?)(?:\s+WHERE|$)', sql, re.IGNORECASE)
    if update_match:
        set_clause = update_match.group(1)
        # Split by comma and clean up
        for col in set_clause.split(','):
            col = col.strip()
            # Extract column name before "="
            col = col.split('=')[0].strip()
            # Remove quotes if present
            col = col.replace('"', '').replace("'", '').replace('`', '')
            if col:
                columns.add(col.lower())
    
    return columns

def get_operation_type(sql: str) -> str:
    """Determine operation type (read, write, or admin)."""
    sql_upper = sql.strip().upper()
    
    # Check for destructive operations
    for keyword in DESTRUCTIVE_KEYWORDS:
        if sql_upper.startswith(keyword):
            return "destructive"
    
    # Check for read-only operations
    for keyword in READ_ONLY_KEYWORDS:
        if sql_upper.startswith(keyword):
            return "read"
    
    # Default to write if not clearly read-only
    return "write"

# --- Main Impact Agent Function ---
def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Impact Agent: Analyzes SQL query for safety, PII exposure, and cost.
    
    Args:
        state: Current state dictionary from LangGraph workflow
        
    Returns:
        Updated state with impact analysis results
    """
    sql_query = state.get("sql", "")
    
    if not sql_query:
        return {
            "impact_analysis": {
                "is_safe": False,
                "risk_level": "high",
                "reason": "No SQL query provided",
                "sensitive_tables_found": [],
                "sensitive_columns_found": [],
                "operation_type": "unknown",
                "cost_estimate": "N/A",
                "warnings": ["No SQL query to analyze"]
            }
        }
    
    # Extract tables and columns
    tables = extract_tables(sql_query)
    columns = extract_columns(sql_query)
    
    # Determine operation type
    operation_type = get_operation_type(sql_query)
    
    # Check for sensitive tables
    sensitive_tables_found = list(tables.intersection(SENSITIVE_TABLES))
    
    # Check for sensitive columns
    sensitive_columns_found = list(columns.intersection(SENSITIVE_COLUMNS))
    
    # Determine safety and risk level
    is_safe = True
    risk_level = "low"
    warnings = []
    
    if sensitive_tables_found:
        is_safe = False
        risk_level = "high"
        warnings.append(f"Access to sensitive tables detected: {', '.join(sensitive_tables_found)}")
    
    if sensitive_columns_found:
        is_safe = False
        risk_level = "high"
        warnings.append(f"Access to sensitive columns detected: {', '.join(sensitive_columns_found)}")
    
    if operation_type == "destructive":
        is_safe = False
        risk_level = "critical"
        warnings.append("Destructive operation detected (DROP/DELETE/UPDATE)")
    
    if operation_type == "write" and not sensitive_tables_found and not sensitive_columns_found:
        risk_level = "medium"
        warnings.append("Write operation detected (may impact performance)")
    
    # Estimate cost (simple heuristic)
    cost_estimate = "low"
    if len(tables) > 5:
        cost_estimate = "medium"
    if len(tables) > 20 or operation_type == "destructive":
        cost_estimate = "high"
    
    # Log the analysis
    print(f"[IMPACT] SQL Query: {sql_query}")
    print(f"[IMPACT] Tables: {list(tables)}")
    print(f"[IMPACT] Columns: {list(columns)}")
    print(f"[IMPACT] Operation: {operation_type}")
    print(f"[IMPACT] Sensitive Tables: {sensitive_tables_found}")
    print(f"[IMPACT] Sensitive Columns: {sensitive_columns_found}")
    print(f"[IMPACT] Risk Level: {risk_level}")
    print(f"[IMPACT] Safe: {is_safe}")
    
    # Return analysis in state
    return {
        "impact_analysis": {
            "is_safe": is_safe,
            "risk_level": risk_level,
            "reason": "Sensitive data access detected" if not is_safe else "Query is safe",
            "sensitive_tables_found": sensitive_tables_found,
            "sensitive_columns_found": sensitive_columns_found,
            "operation_type": operation_type,
            "cost_estimate": cost_estimate,
            "warnings": warnings
        }
    }
