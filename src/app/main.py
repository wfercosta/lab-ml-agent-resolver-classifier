from __future__ import annotations

import concurrent.futures
import time
import structlog

from app.settings.settings import settings
from app.logging import configure_logging
from app.domain.errors import PermanentError, TransientError
from app.prompts.registry import PromptRegistry
from app.infrastructure.aws.sqs_client import SqsQueueAdapter
from app.infrastructure.llm.opeanai_provider import OpenAILangChainAdapter
from app.application.use_cases.process_message import ProcessMessage

log = structlog.get_logger()


def main(): 
    configure_logging(settings.log_level)
    registry = PromptRegistry(prompts_dir=settings.prompts_dir)
    registry.load()

    queue = SqsQueueAdapter(region=settings.aws_region, queue_url=settings.sqs_queue_url)
    
    llm = OpenAILangChainAdapter(
        registry=registry,
        api_key=settings.openai_api_key,
        default_model=settings.openai_default_model,
        default_temperature=settings.openai_default_temperature,
        timeout_seconds=settings.default_timeout_seconds,
        max_repair_attemps=settings.default_max_repair_attemps,
    )

    use_case = ProcessMessage(llm)

    log.info(
        "worker_started",
        queue_url=settings.sqs_queue_url,
        concurrency=settings.worker_concurrency,
        model=settings.openai_model,
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=settings.worker_concurrency) as pool:
        while True:
            messages = queue.receive(
                max_messages=settings.sqs_max_messages,
                wait_time_seconds=settings.sqs_wait_time_seconds,
                visibility_timeout=settings.sqs_visibility_timeout,
            )

            if not messages:
                continue

            futures = []
            for m in messages:
                futures.append(pool.submit(_handle_one, use_case, queue, m.message_id, m.receipt_handle, m.body))

            for f in concurrent.futures.as_completed(futures):
                _ = f.result()


def _handle_one(use_case: ProcessMessage, queue: SqsQueueAdapter, message_id: str, receipt: str, body: str) -> None:
    started = time.time()
    try:
        result = use_case.execute(body, message_id=message_id)
        queue.delete(receipt)
        log.info(
            "message_processed",
            message_id=message_id,
            correlation_id=result.correlation_id,
            intent=result.intent,
            output_len=len(result.output_text or ""),
        )

    except PermanentError as e:
        queue.delete(receipt)
        log.warning("message_permanent_error", message_id=message_id, error=str(e))

    except TransientError as e:
        log.warning("message_transient_error", message_id=message_id, error=str(e))

    except Exception as e:
        log.exception("message_unhandled_error", message_id=message_id, error=str(e))


if __name__ == "__main__":
    main()
