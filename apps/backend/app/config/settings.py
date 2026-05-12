from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "AI Office OS"
    ENV: Literal["development", "production", "test"] = "development"
    LOG_LEVEL: str = "INFO"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    MODEL_PROVIDER: Literal["ollama", "local", "mock"] = "ollama"
    LOCAL_MODE: bool = True

    OLLAMA_MODEL: str = "qwen2.5:7b"
    OLLAMA_URL: str = "http://localhost:11434"

    WORLD_SYNC_INTERVAL_SECONDS: float = Field(default=1.0, gt=0)
    PERSISTENCE_ENABLED: bool = True
    PERSISTENCE_PATH: str = "storage/world_state.json"

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
