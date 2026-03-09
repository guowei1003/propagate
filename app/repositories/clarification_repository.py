from __future__ import annotations

import uuid

from app.db import transaction
from app.repositories.common import dumps_json, loads_json, row_to_dict, utcnow


class ClarificationRepository:
    def create_round(self, task_id: str, questions: list[dict]) -> str:
        round_id = str(uuid.uuid4())
        with transaction() as conn:
            conn.execute(
                """
                INSERT INTO clarification_rounds (
                    id, task_id, status, questions_json, answers_json, created_at
                ) VALUES (?, ?, 'pending', ?, '{}', ?)
                """,
                (round_id, task_id, dumps_json(questions), utcnow()),
            )
        return round_id

    def get_pending_round(self, task_id: str) -> dict | None:
        with transaction() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM clarification_rounds
                WHERE task_id = ? AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (task_id,),
            ).fetchone()
        if not row:
            return None
        payload = row_to_dict(row)
        payload["questions"] = loads_json(payload.pop("questions_json"), [])
        payload["answers"] = loads_json(payload.pop("answers_json"), {})
        return payload

    def list_rounds(self, task_id: str) -> list[dict]:
        with transaction() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM clarification_rounds
                WHERE task_id = ?
                ORDER BY created_at ASC
                """,
                (task_id,),
            ).fetchall()
        payloads = []
        for row in rows:
            item = row_to_dict(row)
            item["questions"] = loads_json(item.pop("questions_json"), [])
            item["answers"] = loads_json(item.pop("answers_json"), {})
            payloads.append(item)
        return payloads

    def answer_round(self, round_id: str, answers: dict[str, str]) -> None:
        with transaction() as conn:
            conn.execute(
                """
                UPDATE clarification_rounds
                SET status = 'answered',
                    answers_json = ?,
                    answered_at = ?
                WHERE id = ?
                """,
                (dumps_json(answers), utcnow(), round_id),
            )

    def get_merged_answers(self, task_id: str) -> dict[str, str]:
        merged: dict[str, str] = {}
        for item in self.list_rounds(task_id):
            merged.update(item["answers"])
        return merged

