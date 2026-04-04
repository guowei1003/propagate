from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.config import BASE_DIR


@dataclass(frozen=True)
class V2Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@127.0.0.1:5432/propagate",
    )
    frontend_dist_dir: Path = BASE_DIR / "frontend" / "dist"
    bundle_root: Path = BASE_DIR / "data" / "bundles"
    runtime_root: Path = BASE_DIR / "data" / "runtime-v2"
    default_system_model: str = os.getenv("LLM_DEFAULT_MODEL", "demo-heuristic")
    runtime_worker_threads: int = int(os.getenv("V2_RUNTIME_WORKER_THREADS", "4"))
    event_stream_poll_interval_sec: float = float(os.getenv("V2_EVENT_STREAM_POLL_INTERVAL_SEC", "1.0"))


v2_settings = V2Settings()
