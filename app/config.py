from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from project root
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    load_dotenv(_env_file)


def _get_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("true", "1", "yes")


@dataclass(frozen=True)
class LLMConfig:
    """LLM provider configuration from environment variables."""
    provider_type: str = os.getenv("LLM_PROVIDER_TYPE", "demo")
    api_base_url: str = os.getenv("LLM_API_BASE_URL", "")
    api_key: str = os.getenv("LLM_API_KEY", "")
    default_model: str = os.getenv("LLM_DEFAULT_MODEL", "demo-heuristic")
    review_model: str = os.getenv("LLM_REVIEW_MODEL", "")
    test_model: str = os.getenv("LLM_TEST_MODEL", "")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
    timeout_sec: int = int(os.getenv("LLM_TIMEOUT_SEC", "300"))

    def to_env_profile(self) -> dict | None:
        """Convert to env_profile dict for LLMService. Returns None if using demo mode."""
        if self.provider_type == "demo":
            return None
        return {
            "provider_type": self.provider_type,
            "api_base_url": self.api_base_url,
            "api_key": self.api_key,
            "default_model": self.default_model,
            "review_model": self.review_model or self.default_model,
            "test_model": self.test_model or self.default_model,
            "temperature": self.temperature,
            "max_retries": self.max_retries,
            "default_timeout_sec": self.timeout_sec,
        }


@dataclass(frozen=True)
class Settings:
    app_name: str = "Propagate"
    database_path: Path = BASE_DIR / "data" / "propagate.db"
    artifacts_root: Path = BASE_DIR / "data" / "artifacts"
    default_model: str = os.getenv("DEFAULT_MODEL", "demo-heuristic")
    default_timeout_sec: int = int(os.getenv("DEFAULT_TIMEOUT_SEC", "300"))
    worker_poll_interval_sec: float = float(os.getenv("WORKER_POLL_INTERVAL_SEC", "1.0"))
    max_worker_concurrency: int = int(os.getenv("MAX_WORKER_CONCURRENCY", "3"))
    event_stream_interval_sec: float = float(os.getenv("EVENT_STREAM_INTERVAL_SEC", "1.0"))
    secret_key: str = os.getenv("SECRET_KEY", "propagate-dev")
    # LLM configuration from environment
    llm: LLMConfig = field(default_factory=LLMConfig)


settings = Settings()

