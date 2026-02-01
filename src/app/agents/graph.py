from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.nodes.resolver import resolver_node
from app.agents.nodes.dedupe import dedupe_node
from app.agents.nodes.classifier import classifier_node
from app.agents.nodes.classifier_judge import classifier_judge_node
from app.agents.nodes.router import route_node
from app.application.ports.llm import LLMPort

def build_graph(llm: LLMPort):
    g = StateGraph(AgentState)

    g.add_node("resolver", resolver_node(llm))
    g.add_node("dedupe", dedupe_node(llm))
    g.add_node("classifier", classifier_node(llm))
    g.add_node("classifier_judge", classifier_judge_node)

    g.set_entry_point("resolver")

    g.add_conditional_edges(
        "classifier",
        route_node,
        {
            "judge": "classifier_judge",
        },
    )
    
    return g.compile()
