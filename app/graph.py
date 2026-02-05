from langgraph.graph import StateGraph, END
from app.core.state import TravelAgentState
from app.engine.nodes import (
    init_node, travel_router_node, trip_planner_node, 
    places_finder_node, confidence_evaluator_node, logistics_critic_node, publisher_node, ask_human_node, failure_handler_node
)

def route_after_planner(state: TravelAgentState):
    return "continue"

def route_after_confidence(state: TravelAgentState):
    if state["confidence_score"] < 0.7:
        return "ask_human"
    return "continue"

def route_after_critic(state: TravelAgentState):
    if state.get("is_approved", False):
        return "approved"
    
    # Se il Critic boccia e abbiamo esaurito i tentativi (e.g. 3)
    if state.get("retry_count", 0) >= 3:
        return "fail"
        
    return "retry"

workflow = StateGraph(TravelAgentState)

workflow.add_node("init", init_node)
workflow.add_node("router", travel_router_node)
workflow.add_node("planner", trip_planner_node)
workflow.add_node("finder", places_finder_node)
workflow.add_node("confidence", confidence_evaluator_node)
workflow.add_node("critic", logistics_critic_node)
workflow.add_node("publisher", publisher_node)
workflow.add_node("ask_human", ask_human_node)
workflow.add_node("failure_handler", failure_handler_node)

workflow.set_entry_point("init")
workflow.add_edge("init", "router")
workflow.add_edge("router", "planner")

workflow.add_conditional_edges(
    "planner",
    route_after_planner, 
    {
        "continue": "finder"         # Vai al Finder
    }
)

workflow.add_edge("finder", "confidence")

workflow.add_conditional_edges(
    "confidence",
    route_after_confidence,
    {
        "ask_human": "ask_human",
        "continue": "critic"
    }
)

workflow.add_conditional_edges(
    "ask_human",
    lambda state: "approved" if state["is_approved"] else "rejected",
    {
        "approved": "finder",   # L'utente ha detto OK --> vai al Finder
        "rejected": "planner"   # L'utent ha dato feedback --> torna al Planner
    }
)

workflow.add_conditional_edges(
    "critic",
    route_after_critic,
    {
        "approved": "publisher", 
        "retry": "planner",
        "fail": "failure_handler"
    }
)

workflow.add_edge("publisher", END)
workflow.add_edge("failure_handler", END)
app = workflow.compile()

if __name__ == "__main__":
    print("TRAVEL AGENT AVVIATO...")
    app.invoke({"retry_count": 0, "is_approved": False})
