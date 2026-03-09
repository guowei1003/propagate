from __future__ import annotations

import uuid

from app.db import transaction
from app.repositories.common import dumps_json, loads_json, row_to_dict, utcnow


class RequirementRepository:
    def next_version(self, task_id: str) -> int:
        with transaction() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(version), 0) AS version FROM task_requirements WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        return int(row["version"]) + 1

    def save_requirement(self, task_id: str, analysis: dict) -> None:
        requirement_id = str(uuid.uuid4())
        version = self.next_version(task_id)
        with transaction() as conn:
            conn.execute(
                """
                INSERT INTO task_requirements (
                    id, task_id, version, goal, scope, inputs_json, outputs_json,
                    constraints_json, acceptance_json, missing_info_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    requirement_id,
                    task_id,
                    version,
                    analysis["goal"],
                    analysis["scope"],
                    dumps_json(analysis["inputs"]),
                    dumps_json(analysis["outputs"]),
                    dumps_json(analysis["constraints"]),
                    dumps_json(analysis["acceptance"]),
                    dumps_json(analysis["missing_info"]),
                    utcnow(),
                ),
            )

    def get_latest(self, task_id: str) -> dict | None:
        with transaction() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM task_requirements
                WHERE task_id = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (task_id,),
            ).fetchone()
        if not row:
            return None
        payload = row_to_dict(row)
        payload["inputs"] = loads_json(payload.pop("inputs_json"), {})
        payload["outputs"] = loads_json(payload.pop("outputs_json"), {})
        payload["constraints"] = loads_json(payload.pop("constraints_json"), {})
        payload["acceptance"] = loads_json(payload.pop("acceptance_json"), {})
        payload["missing_info"] = loads_json(payload.pop("missing_info_json"), [])
        return payload

