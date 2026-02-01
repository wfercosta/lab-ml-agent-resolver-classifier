from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml
from jinja2 import Template

@dataclass(frozen=True)
class PromptSpec:
    id: str
    version: int
    model: Dict[str, Any]
    messages: List[Dict[str, str]]
    output_schema: Optional[Dict[str, any]] = None


class PromptRegistry:
    def __init__(self, prompts_dir: str | Path | None = None):
        if prompts_dir is None:
            prompts_dir = Path(__file__).resolve().parent / "yaml"
        self._dir = Path(prompts_dir)
        self._cache: Dict[str, PromptSpec] = {}

    def load(self) -> None:
        if not self._dir.exists():
            raise FileNotFoundError(f"Prompts dir not found: {self._dir}")

        for path in sorted(self._dir.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            spec = self._parse(data, path.name)
            self._cache[spec.id] = spec

    def get(self, prompt_id: str):
        try:
            return self._cache[prompt_id]
        except KeyError as e:
            raise KeyError(f"Prompt not found: {prompt_id}, Loaded={list(self._cache.keys())}") from e
        
    def render_messages(self, prompt_id: str, variables: Dict[str, Any]) -> List[Dict[str, str]]:
        spec: PromptSpec = self.get(prompt_id)
        rendered: List[Dict[str, str]] = []
        for m in spec.messages:
            rendered.append(
                {
                    "role": m["role"],
                    "content": Template(m["content"]).render(**variables)
                }
            )

        return rendered


    def _parse(self, data: Dict[str, Any], filename: str) -> PromptSpec:
        required = ["id", "version", "messages", "output_schema"]
        for r in required:
            if r not in data:
                raise ValueError(f"Prompt {filename} missing required field: {r}")
            
        if not isinstance(data["messages"], list) or not data["messages"]:
            raise ValueError(f"Prompot {filename} has invalid message")
        
        model = data.get("model", {})
        output_schema = data.get("output_schema", {})
        return PromptSpec(
            id=str(data["id"]),
            version=int(data["version"]),
            messages=data["messages"],
            model=model,
            output_schema=output_schema,
        )
