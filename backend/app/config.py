from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ANTHROPIC_FOUNDRY_API_KEY: str | None = None
    ANTHROPIC_FOUNDRY_RESOURCE: str | None = None

    FOUNDRY_REVIEWER_MODEL: str = "claude-sonnet-4-6"
    FOUNDRY_CONSOLIDATOR_MODEL: str = "claude-sonnet-4-6"

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"
    SNAPSHOT_DIR: str = "./data/snapshots"
    LOG_LEVEL: str = "INFO"

    CORS_ORIGINS: str = "https://localhost:3000"

    REVIEWER_SHOTS: int = 3
    REVIEWER_TEMPERATURE: float = 1.0
    CONSOLIDATOR_TEMPERATURE: float = 0.2

    PACKS_DIR: str = "app/packs"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def packs_path(self) -> Path:
        return Path(self.PACKS_DIR)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
