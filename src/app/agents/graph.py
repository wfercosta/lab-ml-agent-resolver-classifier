from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.application.ports.llm import LLMPort

def build_graph(llm: LLMPort):
    g = StateGraph(AgentState)

    return g.compile()
