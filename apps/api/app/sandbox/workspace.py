from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.config import get_settings


def create_workspace(run_id: str) -> Path:
    settings = get_settings()
    workspace = settings.workspaces_dir / run_id / uuid4().hex
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace
