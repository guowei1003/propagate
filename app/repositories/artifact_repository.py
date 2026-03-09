from __future__ import annotations

import uuid

from app.db import transaction
from app.repositories.common import dumps_json, row_to_dict, utcnow


class ArtifactRepository:
    def create_artifact(
        self,
        task_id: str,
        sub_task_id: str | None,
        artifact_type: str,
        path: str,
        summary: str,
        metadata: dict | None = None,
    ) -> None:
        with transaction() as conn:
            conn.execute(
                """
                INSERT INTO artifacts (id, task_id, sub_task_id, artifact_type, path, summary, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    task_id,
                    sub_task_id,
                    artifact_type,
                    path,
                    summary,
                    dumps_json(metadata or {}),
                    utcnow(),
                ),
            )

    def list_by_task(self, task_id: str) -> list[dict]:
        with transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM artifacts WHERE task_id = ? ORDER BY created_at ASC",
                (task_id,),
            ).fetchall()
        return [row_to_dict(row) for row in rows]

