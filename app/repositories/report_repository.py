from __future__ import annotations

import uuid

from app.db import transaction
from app.repositories.common import dumps_json, row_to_dict, utcnow


class ReportRepository:
    def save_report(self, task_id: str, report_markdown: str, summary: dict) -> None:
        with transaction() as conn:
            existing = conn.execute(
                "SELECT id FROM task_reports WHERE task_id = ?",
                (task_id,),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE task_reports
                    SET report_markdown = ?, summary_json = ?, created_at = ?
                    WHERE task_id = ?
                    """,
                    (report_markdown, dumps_json(summary), utcnow(), task_id),
                )
                return
            conn.execute(
                """
                INSERT INTO task_reports (id, task_id, report_markdown, summary_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), task_id, report_markdown, dumps_json(summary), utcnow()),
            )

    def get_report(self, task_id: str) -> dict | None:
        with transaction() as conn:
            row = conn.execute(
                "SELECT * FROM task_reports WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        return row_to_dict(row) if row else None

