from __future__ import annotations

import structlog

from app.settings.settings import settings
from app.domain.errors import PermanentError, TransientError
from app.prompts.registry import PromptRegistry
from app.infrastructure.llm.opeanai_provider import OpenAILangChainAdapter

log = structlog.get_logger()


def main(): 
    registry = PromptRegistry(prompts_dir=settings.prompts_dir)
    registry.load()

    llm = OpenAILangChainAdapter(
        registry=registry,
        api_key=settings.openai_api_key,
        default_model=settings.openai_default_model,
        default_temperature=settings.openai_default_temperature,
        timeout_seconds=settings.default_timeout_seconds,
        max_repair_attemps=settings.default_max_repair_attemps,
    )
if __name__ == "__main__":
    main()
