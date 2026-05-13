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
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    LLM_PROVIDER: Literal[
        "mock",
        "ollama",
    ] = "mock"
    LLM_REAL_CALLS_ENABLED: bool = False
    LLM_TIMEOUT_SECONDS: float = Field(default=15.0, gt=0)
    LLM_PROMPT_LOG_ENABLED: bool = True
    LLM_MAX_PROMPT_CHARS: int = Field(default=12000, gt=0)
    LLM_REASONING_ENABLED: bool = False
    LLM_REASONING_RATE_LIMIT_PER_MINUTE: int = Field(default=20, gt=0)
    LLM_REASONING_RATE_LIMIT_PER_PURPOSE: int = Field(default=8, gt=0)
    LLM_REASONING_CACHE_TTL_SECONDS: int = Field(default=120, gt=0)
    LLM_SUGGESTION_TTL_MINUTES: int = Field(default=240, gt=0)
    LLM_SUGGESTION_MAX_HISTORY: int = Field(default=200, gt=0)

    WORLD_SYNC_INTERVAL_SECONDS: float = Field(default=1.0, gt=0)
    PERSISTENCE_ENABLED: bool = True
    PERSISTENCE_PATH: str = "storage/world_state.json"
    TOOL_POLICY_PROFILE: Literal[
        "locked_down",
        "safe_local",
        "assisted",
        "autonomous_safe",
    ] = "safe_local"

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
