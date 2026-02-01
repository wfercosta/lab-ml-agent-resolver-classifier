from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    log_level: str = "info"

    openai_api_key: str
    openai_default_model: str = "gpt-4o-mini"
    openai_default_temperature: float = 0.2
    openai_default_embedding_model: str = 'text-embedding-3-small'

    sqs_queue_url: str
    sqs_max_messages: int = 10
    sqs_wait_time_seconds: int = 20
    sqs_visibility_timeout: int = 120

    worker_concurrency: int = 4
    
    default_timeout_seconds: int = 30
    default_max_repair_attemps: int = 1
    
    pg_database_url: str
    pg_vector_collection_name: str = "gpt5_collection"

    prompts_dir: str | None = None    


settings = Settings()
