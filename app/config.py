from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


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


settings = Settings()

