from __future__ import annotations

import threading
import uuid

from app.db import transaction
from app.enums import (
    SUBTASK_STATUS_COMPLETED,
    SUBTASK_STATUS_PENDING,
    SUBTASK_STATUS_READY,
    SUBTASK_STATUS_RUNNING,
)
from app.repositories.common import dumps_json, loads_json, row_to_dict, utcnow


_claim_lock = threading.Lock()


class SubTaskRepository:
    def replace_subtasks(
        self,
        task_id: str,
        items: list[dict],
        dependencies: list[tuple[str, str]],
    ) -> None:
        with transaction() as conn:
            conn.execute("DELETE FROM sub_task_dependencies WHERE task_id = ?", (task_id,))
            conn.execute("DELETE FROM sub_tasks WHERE task_id = ?", (task_id,))
            now = utcnow()
            for item in items:
                conn.execute(
                    """
                    INSERT INTO sub_tasks (
                        id, task_id, name, description, category, status, priority,
                        sequence_no, agent_template, skill_bindings_json, acceptance_json,
                        input_context_json, output_summary_json, retry_count, max_retries,
                        timeout_sec, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["id"],
                        task_id,
                        item["name"],
                        item["description"],
                        item["category"],
                        SUBTASK_STATUS_PENDING,
                        item["priority"],
                        item["sequence_no"],
                        item["agent_template"],
                        dumps_json(item["skill_bindings"]),
                        dumps_json(item["acceptance"]),
                        dumps_json(item["input_context"]),
                        dumps_json({}),
                        0,
                        item["max_retries"],
                        item["timeout_sec"],
                        now,
                        now,
                    ),
                )
            for from_id, to_id in dependencies:
                conn.execute(
                    """
                    INSERT INTO sub_task_dependencies (
                        id, task_id, from_sub_task_id, to_sub_task_id, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (str(uuid.uuid4()), task_id, from_id, to_id, now),
                )

    def list_by_task(self, task_id: str) -> list[dict]:
        with transaction() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM sub_tasks
                WHERE task_id = ?
                ORDER BY sequence_no ASC, created_at ASC
                """,
                (task_id,),
            ).fetchall()
        payloads = []
        for row in rows:
            payloads.append(self._inflate(row_to_dict(row)))
        return payloads

    def get_subtask(self, subtask_id: str) -> dict | None:
        with transaction() as conn:
            row = conn.execute(
                "SELECT * FROM sub_tasks WHERE id = ?",
                (subtask_id,),
            ).fetchone()
        return self._inflate(row_to_dict(row)) if row else None

    def _inflate(self, payload: dict) -> dict:
        payload["skill_bindings"] = loads_json(payload.pop("skill_bindings_json"), [])
        payload["acceptance"] = loads_json(payload.pop("acceptance_json"), {})
        payload["input_context"] = loads_json(payload.pop("input_context_json"), {})
        payload["output_summary"] = loads_json(payload.pop("output_summary_json"), {})
        return payload

    def list_dependencies(self, task_id: str) -> list[dict]:
        with transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM sub_task_dependencies WHERE task_id = ?",
                (task_id,),
            ).fetchall()
        return [row_to_dict(row) for row in rows]

    def mark_ready(self, subtask_id: str) -> None:
        with transaction() as conn:
            conn.execute(
                """
                UPDATE sub_tasks
                SET status = ?, updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (SUBTASK_STATUS_READY, utcnow(), subtask_id, SUBTASK_STATUS_PENDING),
            )

    def mark_running(self, subtask_id: str) -> None:
        with transaction() as conn:
            conn.execute(
                """
                UPDATE sub_tasks
                SET status = ?, started_at = COALESCE(started_at, ?), updated_at = ?
                WHERE id = ?
                """,
                (SUBTASK_STATUS_RUNNING, utcnow(), utcnow(), subtask_id),
            )

    def mark_retry_pending(self, subtask_id: str, retry_count: int) -> None:
        with transaction() as conn:
            conn.execute(
                """
                UPDATE sub_tasks
                SET status = 'RETRY_PENDING', retry_count = ?, updated_at = ?
                WHERE id = ?
                """,
                (retry_count, utcnow(), subtask_id),
            )

    def mark_completed(self, subtask_id: str, output_summary: dict) -> None:
        with transaction() as conn:
            conn.execute(
                """
                UPDATE sub_tasks
                SET status = ?, output_summary_json = ?, completed_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    SUBTASK_STATUS_COMPLETED,
                    dumps_json(output_summary),
                    utcnow(),
                    utcnow(),
                    subtask_id,
                ),
            )

    def mark_needs_human_review(self, subtask_id: str, retry_count: int, summary: dict) -> None:
        with transaction() as conn:
            conn.execute(
                """
                UPDATE sub_tasks
                SET status = 'NEEDS_HUMAN_REVIEW',
                    retry_count = ?,
                    output_summary_json = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (retry_count, dumps_json(summary), utcnow(), subtask_id),
            )

    def update_output_summary(self, subtask_id: str, output_summary: dict) -> None:
        with transaction() as conn:
            conn.execute(
                """
                UPDATE sub_tasks
                SET output_summary_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (dumps_json(output_summary), utcnow(), subtask_id),
            )

    def claim_ready(self, limit: int) -> list[dict]:
        with _claim_lock:
            with transaction() as conn:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM sub_tasks
                    WHERE status IN (?, 'RETRY_PENDING')
                    ORDER BY priority ASC, sequence_no ASC, created_at ASC
                    LIMIT ?
                    """,
                    (SUBTASK_STATUS_READY, limit),
                ).fetchall()
                results = []
                for row in rows:
                    item = row_to_dict(row)
                    conn.execute(
                        "UPDATE sub_tasks SET status = ?, updated_at = ? WHERE id = ?",
                        (SUBTASK_STATUS_RUNNING, utcnow(), item["id"]),
                    )
                    item["status"] = SUBTASK_STATUS_RUNNING
                    results.append(self._inflate(item))
        return results

    def count_by_status(self, task_id: str, status: str) -> int:
        with transaction() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM sub_tasks WHERE task_id = ? AND status = ?",
                (task_id, status),
            ).fetchone()
        return int(row["count"])

    def task_is_terminal(self, task_id: str) -> bool:
        with transaction() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM sub_tasks
                WHERE task_id = ? AND status NOT IN (?, 'NEEDS_HUMAN_REVIEW')
                """,
                (task_id, SUBTASK_STATUS_COMPLETED),
            ).fetchone()
        return int(row["count"]) == 0

    def get_task_progress(self, task_id: str) -> float:
        with transaction() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS completed
                FROM sub_tasks
                WHERE task_id = ?
                """,
                (SUBTASK_STATUS_COMPLETED, task_id),
            ).fetchone()
        total = int(row["total"])
        completed = int(row["completed"] or 0)
        return 0.0 if total == 0 else round((completed / total) * 100, 2)

