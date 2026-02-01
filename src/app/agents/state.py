from __future__ import annotations
from typing import TypedDict, Optional, Dict, Any


class AgentState(TypedDict, total=False):
    correlation_id: str
    input_text: str
    context: Dict[str, Any]
    final_output: Dict[str, Any]
    agent_resolver: Optional[str]
    agent_dedupe: Optional[str]
    agent_classifier: Optional[str]
    agent_classifier_judge: Optional[str]