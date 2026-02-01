from langgraph.graph import StateGraph, END
from app.core.state import TravelAgentState
from app.engine.nodes import (
    init_node, travel_router_node, trip_planner_node, 
    places_finder_node, logistics_critic_node, publisher_node
)

def check_critic_verdict(state: TravelAgentState):
    if state.get("is_approved", False) or state.get("retry_count", 0) >= 3:
        return "approved"
    return "rejected"

workflow = StateGraph(TravelAgentState)

workflow.add_node("init", init_node)
workflow.add_node("router", travel_router_node)
workflow.add_node("planner", trip_planner_node)
workflow.add_node("finder", places_finder_node)
workflow.add_node("critic", logistics_critic_node)
workflow.add_node("publisher", publisher_node)

workflow.set_entry_point("init")
workflow.add_edge("init", "router")
workflow.add_edge("router", "planner")
workflow.add_edge("planner", "finder")
workflow.add_edge("finder", "critic")

workflow.add_conditional_edges(
    "critic",
    check_critic_verdict,
    {"approved": "publisher", "rejected": "planner"}
)

workflow.add_edge("publisher", END)
app = workflow.compile()

if __name__ == "__main__":
    print("🤖 TRAVEL AGENT AVVIATO...")
    app.invoke({"retry_count": 0, "is_approved": False})