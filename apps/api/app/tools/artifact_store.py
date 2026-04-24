from __future__ import annotations

import hashlib
from pathlib import Path

from app.config import get_settings


def write_artifact(run_id: str, name: str, content: bytes) -> tuple[str, str]:
    settings = get_settings()
    run_dir = settings.artifacts_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / name
    path.write_bytes(content)
    sha = hashlib.sha256(content).hexdigest()
    return str(path), sha


def read_artifact(path: str) -> bytes:
    return Path(path).read_bytes()
