from __future__ import annotations

import json
from typing import Any, Dict

from app.application.ports.llm import LLMPort
from app.agents.graph import build_graph
from app.domain.models import WorkItem, WorkResult
from app.domain.errors import PermanentError

class ProcessMessage:
    def __init__(self, llm: LLMPort):
        self._llm = llm
        self._graph = build_graph(llm)

    def execute(self, raw_body: str, message_id:str) -> WorkResult:
        item = self._parse_body(raw_body, message_id)

        init_state = {
            "correlation_id": item.correlation_id or message_id,
            "input_text": item.input_text,
            "context": item.metadata
        }

        final_state = self._graph.invoke(init_state)

        return WorkResult(
            correlation_id=final_state.get("correlation_id", message_id),
            output_text=final_state.get("final_output", ""),
            intent=final_state.get("intent"),
            details={
                "confidence": final_state.get("confidence"),
                "agent_a": final_state.get("agent_a"),
                "agent_b": final_state.get("agent_b"),
            },
        )


    def _parse_body(self, raw_body: str, message_id:str) -> WorkItem:
        try:
            data: Dict[str, Any] = json.loads(raw_body)
            return WorkItem(
                correlation_id=data.get("correlation_id", message_id)
                input_text=data["input_text"],
                metadata=data.get("metadata", {})
            )
        except KeyError as e:
            raise PermanentError(f"missing field: {e}") from e
        except Exception as e:
            raise PermanentError(f"invalid json: {e}") from e


