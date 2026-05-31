from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "postgresql://linkforge:change_this_password@localhost:5432/linkforge"
    secret_key: str = "change-this-to-a-secure-random-32-char-string-in-prod"
    log_level: str = "INFO"
    playwright_headless: bool = True
    embedding_model: str = "all-MiniLM-L6-v2"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_api_base: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
