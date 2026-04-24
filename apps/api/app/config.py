from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PROPAGATE_",
        extra="ignore",
    )

    app_name: str = "Propagate Agent Harness"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    sql_echo: bool = False

    database_url: str = "sqlite+aiosqlite:///./data/propagate.db"
    checkpoint_database_url: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    default_provider: str = "mock"
    default_model: str = "gpt-4.1-mini"

    artifacts_dir: Path = Field(default=ROOT_DIR / "data" / "artifacts")
    workspaces_dir: Path = Field(default=ROOT_DIR / "data" / "workspaces")
    max_run_replans: int = 3
    max_step_retries: int = 2
    default_step_timeout_sec: int = 180
    default_sandbox_cpu_limit: float = 1.0
    default_sandbox_memory_limit_mb: int = 512
    default_http_methods: list[str] = Field(default_factory=lambda: ["GET", "POST"])
    poll_interval_ms: int = 500

    def resolved_checkpoint_database_url(self) -> str:
        if self.checkpoint_database_url:
            return self.checkpoint_database_url
        if self.database_url.startswith("postgresql+asyncpg://"):
            return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    settings.workspaces_dir.mkdir(parents=True, exist_ok=True)
    return settings
