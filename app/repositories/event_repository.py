from __future__ import annotations

from app.db import transaction
from app.repositories.common import dumps_json, row_to_dict, utcnow


class EventRepository:
    def append(
        self,
        task_id: str,
        event_type: str,
        message: str,
        *,
        level: str = "info",
        sub_task_id: str | None = None,
        payload: dict | None = None,
    ) -> int:
        with transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO task_events (
                    task_id, sub_task_id, event_type, level, message, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    sub_task_id,
                    event_type,
                    level,
                    message,
                    dumps_json(payload or {}),
                    utcnow(),
                ),
            )
            return int(cursor.lastrowid)

    def list_by_task(self, task_id: str, *, after_id: int | None = None, limit: int = 300) -> list[dict]:
        query = """
            SELECT *
            FROM task_events
            WHERE task_id = ?
        """
        params: list = [task_id]
        if after_id is not None:
            query += " AND id > ?"
            params.append(after_id)
        query += " ORDER BY id ASC LIMIT ?"
        params.append(limit)
        with transaction() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [row_to_dict(row) for row in rows]

