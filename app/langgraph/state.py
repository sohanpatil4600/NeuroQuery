from typing import TypedDict, Any, List

class BIState(TypedDict):
    tenant_id: str
    user_id: str
    question: str
    corrected_question: str # Added to track AI normalization
    history: List[Any]
    metadata: dict
    rag_context: str
    sql: str
    error: str # Track DB errors for self-healing
    retry_count: int # Track number of correction attempts
    result: Any
    response: dict
