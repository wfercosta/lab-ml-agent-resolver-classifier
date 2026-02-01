from __future__ import annotations

import structlog

from app.settings.settings import settings

from app.prompts.registry import PromptRegistry
from app.domain.errors import PermanentError, TransientError

log = structlog.get_logger()


def main(): 
    registry = PromptRegistry(prompts_dir=settings.prompts_dir)
    registry.load()
    

    print(registry.get(prompt_id="resolver"))

    
    # llm = OpenAILangChainAdapter(
    #     registry=registry,
    #     model=settings.openai_model,
    #     temperature=settings.openai_temperature,
    #     api_key=settings.openai_api_key,
    # )

if __name__ == "__main__":
    main()
