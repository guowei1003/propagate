from __future__ import annotations

import uuid

from app.db import transaction
from app.repositories.common import dumps_json, utcnow


class RunRepository:
    def start_run(
        self,
        task_id: str,
        sub_task_id: str | None,
        agent_type: str,
        model: str,
        input_payload: dict,
    ) -> str:
        run_id = str(uuid.uuid4())
        with transaction() as conn:
            conn.execute(
                """
                INSERT INTO agent_runs (
                    id, task_id, sub_task_id, agent_type, model, status,
                    input_json, output_json, error_json, started_at
                ) VALUES (?, ?, ?, ?, ?, 'RUNNING', ?, '{}', '{}', ?)
                """,
                (
                    run_id,
                    task_id,
                    sub_task_id,
                    agent_type,
                    model,
                    dumps_json(input_payload),
                    utcnow(),
                ),
            )
        return run_id

    def finish_run(self, run_id: str, status: str, output_payload: dict | None = None, error_payload: dict | None = None) -> None:
        with transaction() as conn:
            conn.execute(
                """
                UPDATE agent_runs
                SET status = ?, output_json = ?, error_json = ?, completed_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    dumps_json(output_payload or {}),
                    dumps_json(error_payload or {}),
                    utcnow(),
                    run_id,
                ),
            )

