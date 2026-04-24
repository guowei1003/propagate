from __future__ import annotations

from pathlib import Path


def write_workspace_file(workspace_dir: Path, name: str, content: str) -> Path:
    path = workspace_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def read_workspace_file(workspace_dir: Path, name: str) -> str:
    return (workspace_dir / name).read_text()
