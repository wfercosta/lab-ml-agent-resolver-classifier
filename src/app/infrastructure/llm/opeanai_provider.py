from __future__ import annotations
from typing import Dict, List, Any, Type
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from pydantic import BaseModel, ValidationError, create_model

import json
import structlog

from langchain_openai import ChatOpenAI

from app.application.ports.llm import LLMPort, LLMRequest, LLMResponse
from app.prompts.registry import PromptRegistry
from app.domain.errors import PermanentError, TransientError

log = structlog.get_logger()


def _pydantic_model_from_json_schema(name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
    if schema.get("type") != "object":
        raise PermanentError("Only 'type: object' schemas are supported")

    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    additional = schema.get("additionalProperties", True)

    fields: Dict[str, tuple[Any, Any]] = {}
    for key, spec in props.items():
        t = spec.get("type")
        py_type = {
            "string": str,
            "number": float,
            "integer": int,
            "boolean": bool,
            "object": dict,
            "array": list,
        }.get(t, Any)

        default = None
        fields[key] = (py_type, default)

    Model = create_model(name, **fields)

    if additional is False:
        Model.model_config["extra"] = "forbid"

    return Model

def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        # remove ```json ... ```
        t = t.strip("`")
        # pode ficar "json\n{...}"
        if "\n" in t:
            t = t.split("\n", 1)[1]
    return t.strip()


def _extract_json(text: str) -> Any:
    """
    Parse simples: espera JSON puro.
    Se o modelo devolver lixo extra, você pode evoluir com heurísticas/regex.
    """
    t = _strip_code_fences(text)
    return json.loads(t)

def _repair_json(self, bad_text: str, schema: Dict[str, Any], req: LLMRequest) -> str:
        """
        Faz uma segunda chamada pedindo para "consertar" o JSON.
        Mantém o significado, remove lixo e retorna JSON válido.
        """
        repair_prompt_id = "__repair__"

        # Prompt inline (poderia virar YAML também)
        messages = [
            {"role": "system", "content": "Você é um reparador de JSON. Retorne APENAS JSON válido."},
            {
                "role": "user",
                "content": (
                    "Corrija o JSON abaixo para obedecer ao schema. "
                    "Não adicione campos além do permitido. "
                    "Retorne somente JSON.\n\n"
                    f"SCHEMA:\n{json.dumps(schema, ensure_ascii=False)}\n\n"
                    f"BAD_OUTPUT:\n{bad_text}"
                ),
            },
        ]

        try:
            resp = self._client.invoke(messages)
            text = resp.content if hasattr(resp, "content") else str(resp)
            log.info("llm_structured_repair_ok", correlation_id=req.correlation_id, prompt_id=req.prompt_id)
            return text
        except Exception as e:
            raise TransientError(f"repair_failed: {e}") from e

class OpenAILangChainAdapter(LLMPort):
    def __init__(
        self,
        registry: PromptRegistry,
        api_key: str,
        default_model: str,
        default_temperature: float,
        timeout_seconds: int = 30,
        max_repair_attemps: int = 1,
    ):
        self._registry = registry
        self._default_model = default_model
        self._default_temperature = default_temperature
        self._max_repair_attempts = max_repair_attemps


        self._client = ChatOpenAI(
            api_key=api_key,
            model=default_model,
            temperature=default_temperature,
            timeout=timeout_seconds
        )

    def _client_for(self, model:str, temperature: float) -> ChatOpenAI:
        if model == self._default_model and temperature == self._default_temperature:
            return self._client
        
        return ChatOpenAI(
            api_key=self._client.openai_api_key,
            model=model,
            temperature=temperature,
            timeout=self._client.timeout,
        )
    
    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type(TransientError),


    )
    def invoke_text(self, req: LLMRequest) -> LLMResponse:
        spec = self._registry.get(req.prompt_id)

        model = req.model or self._default_model
        temperature = req.temperature if req.temperature is not None else spec.model.get("temperature", self._lldefault_temperature)
        client = self._client_for(model=model, temperature=temperature)

        messages = self._registry.render_messages(req.prompt_id, req.variables)

        try:
            resp = client.invoke(messages)
            text = resp.content if hasattr(resp, "content") else str(resp)

            usage = getattr(resp, "usage_metadata", None)

            log.info(
                "llm_invoke_text_ok",
                correlation_id=req.correlation_id,
                prompt_id=req.prompt_id,
                model=model
            )

            return LLMResponse(text=text, raw=resp, model=model, usage=usage)
        
        except Exception as e:
            
            msg = str(e).lower()

            if "autentication" in msg or "invalid api key" in msg:
                raise PermanentError(f"openai_auth_error: {e}") from e
            
            if "rate limit" in msg or "timeout" in msg:
                raise TransientError(f"openai_transient_error: {e}") from e
            
            raise TransientError(f"openaai_error: {e}") from e
        
    def invoke_structured(self, req: LLMRequest) -> Dict[str, Any]:
        spec = self._registry.get(req.prompt_id)

        if not spec.output_schema:

            resp = self.invoke_text(req)

            try:
                return _extract_json(resp.text)
            except Exception:
                return {"value": resp.text}
            
        if not isinstance(spec.output_schema, dict):
            raise PermanentError(f"prompt {req.prompt_id} output_schema missing json_schema")
        
        Model = _pydantic_model_from_json_schema(req.prompt_id, spec.output_schema)

        # 1) tentativa normal
        resp = self.invoke_text(req)
        parsed = self._parse_and_validate(resp.text, Model, req)

        if parsed is not None:
            return parsed

        # 2) repair (opcional)
        for attempt in range(self._max_repair_attempts):
            repaired = self._repair_json(resp.text, spec.output_schema, req)
            parsed2 = self._parse_and_validate(repaired, Model, req)
            if parsed2 is not None:
                return parsed2

        # se não rolou, é transient (modelo não obedeceu / output “quebrado”)
        raise TransientError(f"structured_output_failed for prompt={req.prompt_id}")
        

