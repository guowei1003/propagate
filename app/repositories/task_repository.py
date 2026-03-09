from __future__ import annotations

import uuid

from app.db import transaction
from app.enums import TASK_PHASE_REQUIREMENT_ANALYZING, TASK_STATUS_CREATED
from app.repositories.common import row_to_dict, utcnow


class TaskRepository:
    def create_task(self, title: str, prompt: str, env_profile_id: str) -> str:
        task_id = str(uuid.uuid4())
        now = utcnow()
        with transaction() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    id, title, prompt, status, current_phase, env_profile_id,
                    progress_percent, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    title,
                    prompt,
                    TASK_STATUS_CREATED,
                    TASK_PHASE_REQUIREMENT_ANALYZING,
                    env_profile_id,
                    0.0,
                    now,
                    now,
                ),
            )
        return task_id

    def list_tasks(self) -> list[dict]:
        with transaction() as conn:
            rows = conn.execute(
                """
                SELECT t.*,
                    (SELECT COUNT(*) FROM sub_tasks st WHERE st.task_id = t.id) AS subtask_count,
                    (SELECT COUNT(*) FROM sub_tasks st WHERE st.task_id = t.id AND st.status = 'COMPLETED') AS completed_subtask_count
                FROM tasks t
                ORDER BY t.created_at DESC
                """
            ).fetchall()
        return [row_to_dict(row) for row in rows]

    def get_task(self, task_id: str) -> dict | None:
        with transaction() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return row_to_dict(row) if row else None

    def update_task(
        self,
        task_id: str,
        *,
        status: str | None = None,
        current_phase: str | None = None,
        progress_percent: float | None = None,
        failure_reason: str | None = None,
        completed: bool = False,
    ) -> None:
        current = self.get_task(task_id)
        if not current:
            return
        values = {
            "status": status or current["status"],
            "current_phase": current_phase or current["current_phase"],
            "progress_percent": progress_percent if progress_percent is not None else current["progress_percent"],
            "failure_reason": failure_reason if failure_reason is not None else current["failure_reason"],
            "updated_at": utcnow(),
            "completed_at": utcnow() if completed else current["completed_at"],
            "id": task_id,
        }
        with transaction() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = :status,
                    current_phase = :current_phase,
                    progress_percent = :progress_percent,
                    failure_reason = :failure_reason,
                    updated_at = :updated_at,
                    completed_at = :completed_at
                WHERE id = :id
                """,
                values,
            )

