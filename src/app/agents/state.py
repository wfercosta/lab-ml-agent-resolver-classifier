from __future__ import annotations
from typing import TypedDict, Optional, Dict, Any


class AgentState(TypedDict, total=False):
    correlation_id: str
    input_text: str
    intent: Optional[str]
    confidence: Optional[float]
    agent_a: Optional[str]
    agent_b: Optional[str]
    final_output: Optional[str]
    context: Dict[str, Any]