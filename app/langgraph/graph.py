from langgraph.graph import StateGraph
from app.langgraph.state import BIState
from app.agents import metadata_agent, rag_agent, sql_agent, impact_agent, execute_agent, bi_agent

graph = StateGraph(BIState)
graph.add_node("metadata", metadata_agent.run)
graph.add_node("rag", rag_agent.run)
graph.add_node("sql", sql_agent.run)
graph.add_node("impact", impact_agent.run)
graph.add_node("execute", execute_agent.run)
graph.add_node("bi", bi_agent.run)

graph.set_entry_point("metadata")
graph.add_edge("metadata", "rag")
graph.add_edge("rag", "sql")
graph.add_edge("sql", "impact")
graph.add_edge("impact", "execute")

# --- REFLEXION LOOP (Self-Healing) ---
def should_continue(state):
    # If there is an error and we haven't hit the retry limit, go back to SQL Agent
    if state.get("error") and state.get("retry_count", 0) < 2:
        print(f"--- REFLEXION TRIGGERED (Attempt {state['retry_count']}) ---")
        return "retry"
    return "end"

graph.add_conditional_edges(
    "execute",
    should_continue,
    {
        "retry": "sql",
        "end": "bi"
    }
)

bi_graph = graph.compile()
