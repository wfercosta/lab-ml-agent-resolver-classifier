# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the application

Copy `.env.example` to `.env` and fill in the required values (at minimum `OPENAI_API_KEY`, `SQS_QUEUE_URL`, and `PG_DATABASE_URL`).

```bash
# Install dependencies
pip install -r requirements.txt

# Start Postgres with pgvector (required if using vector features)
docker compose up -d

# Run the worker
python -m app.main
```

The entrypoint is `src/app/main.py`. Run from the `src/` directory or set `PYTHONPATH=src`.

## Architecture overview

This is a **SQS-driven multi-agent worker** that processes incoming text messages through a LangGraph pipeline.

### Flow

1. `main.py` — polls SQS in a thread pool (`WORKER_CONCURRENCY` workers)
2. `ProcessMessage.execute()` — parses SQS message body (JSON with `input_text`, optional `correlation_id` and `metadata`), invokes the LangGraph
3. **LangGraph pipeline** (`agents/graph.py`):
   - `resolver` → `dedupe` → `classifier` → *(conditional)* → `classifier_judge` or `END`
   - The `route_node` routes to `classifier_judge` only when `agent_classifier` has a value
4. Each node calls `llm.invoke_structured()` with a `prompt_id` that maps to a YAML file

### Key abstractions

- **`LLMPort`** (`application/ports/llm.py`) — protocol for LLM interactions. `OpenAILangChainAdapter` is the only implementation; it uses LangChain's `ChatOpenAI` with tenacity retries on `TransientError`.
- **`QueuePort`** (`application/ports/queue.py`) — protocol for queue interactions. `SqsQueueAdapter` is the only implementation.
- **`PromptRegistry`** (`prompts/registry.py`) — loads all `*.yaml` files from `prompts/yaml/` at startup. Prompts are Jinja2-templated and resolved by `prompt_id`. Each YAML must have `id`, `version`, `messages`, and `output_schema` fields.
- **`AgentState`** — TypedDict shared across all graph nodes. Each node writes its result to its own key (`agent_resolver`, `agent_dedupe`, `agent_classifier`, `agent_classifier_judge`).

### Error handling

- `PermanentError` — message is deleted from SQS without retry (bad input, schema errors, auth failures)
- `TransientError` — message is left in SQS for retry (network errors, rate limits, malformed LLM output). The LLM adapter auto-retries up to 3 times with exponential backoff via tenacity.
- `invoke_structured` has a JSON repair loop: if the LLM returns malformed JSON, it makes a second "repair" call (up to `DEFAULT_MAX_REPAIR_ATTEMPS` times).

### Prompt YAML format

Each prompt file under `src/app/prompts/yaml/` follows this schema:

```yaml
id: <prompt-id>           # must match the prompt_id used in node code
version: 1
model:
  temperature: 0.2
  max_tokens: 512
messages:
  - role: system
    content: |
      ...
  - role: user
    content: |
      {{ input_text }}    # Jinja2 variables
output_schema:            # JSON Schema (type: object only)
  type: object
  required: [field1]
  properties:
    field1:
      type: string
```

### Settings

All configuration is via environment variables (or `.env`). Managed by `pydantic-settings` in `settings/settings.py`. The `openai_model` attribute referenced in `main.py` log line is a bug — the correct attribute is `openai_default_model`.
