from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.repositories.artifact_repository import ArtifactRepository


class ArtifactService:
    def __init__(self) -> None:
        self.repository = ArtifactRepository()

    def save_text_artifact(
        self,
        *,
        task_id: str,
        sub_task_id: str | None,
        artifact_type: str,
        filename: str,
        content: str,
        summary: str,
        metadata: dict | None = None,
    ) -> str:
        folder = settings.artifacts_root / task_id
        if sub_task_id:
            folder = folder / sub_task_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / filename
        path.write_text(content, encoding="utf-8")
        self.repository.create_artifact(
            task_id=task_id,
            sub_task_id=sub_task_id,
            artifact_type=artifact_type,
            path=str(path),
            summary=summary,
            metadata=metadata or {},
        )
        return str(path)


artifact_service = ArtifactService()

