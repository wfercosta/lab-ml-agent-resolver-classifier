from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    log_level: str = "info"

    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.2
    openai_embedding_model: str = 'text-embedding-3-small'

    pg_database_url: str
    pg_vector_collection_name: str = "gpt5_collection"

    prompts_dir: str | None = None    


settings = Settings()
