from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Protocol

@dataclass(frozen=True)
class LLMRequest:
    prompt_id: str
    variables: Dict[str, Any]
    correlation_id: Optional[str] = None
    temperature: Optional[float] = None
    model: Optional[str] = None

@dataclass(frozen=True)
class LLMResponse:
    text: str
    raw: Any
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None


class LLMPort(Protocol):
    def invoke_text(self, req: LLMRequest) -> LLMResponse:
        """Executa um prompt e retorna a resposta como texto."""
        ...
        pass

    def invoke_structured(self, req: LLMRequest) -> Dict[str, Any]:
        """
        Executa um prompt e retorna um dict validado (usa output_schema do YAML).
        Deve lançar:
          - PermanentError: input/prompt inválido, schema impossível, etc.
          - TransientError: falha de rede, rate limit, parsing reparável, etc.
        """
        ...
        pass