from app.agents.state import AgentState

def route_node(state: AgentState) -> str:
    classifier = state.get("agent_classifier")

    if classifier:
     return "judge"
    
    return "end"