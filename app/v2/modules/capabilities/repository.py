from __future__ import annotations

import uuid
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from app.v2.core.db import dumps_json, fetch_all, fetch_one, execute, loads_json
from app.v2.core.errors import NotFoundError


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


class CapabilityRepository:
    def list_capabilities(self, *, capability_type: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        where: list[str] = []
        params: list[Any] = []
        if capability_type:
            where.append("c.type = %s")
            params.append(capability_type)
        if status:
            where.append("v.status = %s")
            params.append(status)
        where_clause = f"WHERE {' AND '.join(where)}" if where else ""
        rows = fetch_all(
            f"""
            SELECT c.*, v.id AS version_id, v.version, v.status, v.content_hash, v.rendered_spec,
                   v.risk_score, v.source_task_id, v.source_run_id, v.default_model_selector,
                   v.generation_model, v.generation_prompt, v.generation_raw_output, v.validation_summary
            FROM capabilities c
            JOIN capability_versions v ON v.id = c.latest_version_id
            {where_clause}
            ORDER BY c.created_at DESC
            """,
            tuple(params),
        )
        return [self._decode(row) for row in rows]

    def get_capability(self, capability_id: str) -> dict[str, Any]:
        row = fetch_one(
            """
            SELECT c.*, v.id AS version_id, v.version, v.status, v.content_hash, v.rendered_spec,
                   v.risk_score, v.source_task_id, v.source_run_id, v.default_model_selector,
                   v.generation_model, v.generation_prompt, v.generation_raw_output, v.validation_summary
            FROM capabilities c
            JOIN capability_versions v ON v.id = c.latest_version_id
            WHERE c.id = %s
            """,
            (capability_id,),
        )
        if not row:
            raise NotFoundError(f"Capability {capability_id} not found.")
        return self._decode(row)

    def get_version(self, version_id: str) -> dict[str, Any]:
        row = fetch_one("SELECT * FROM capability_versions WHERE id = %s", (version_id,))
        if not row:
            raise NotFoundError(f"Capability version {version_id} not found.")
        return self._decode(row)

    def create_capability(
        self,
        *,
        capability_type: str,
        name: str,
        description: str,
        rendered_spec: dict[str, Any],
        risk_score: int,
        source_task_id: str | None,
        source_run_id: str | None,
        default_model_selector: str,
        generation_model: str,
        generation_prompt: str,
        generation_raw_output: str,
        validation_summary: dict[str, Any],
    ) -> dict[str, Any]:
        capability_id = str(uuid.uuid4())
        version_id = str(uuid.uuid4())
        now = utcnow()
        rendered_spec_json = dumps_json(rendered_spec)
        content_hash = sha256(rendered_spec_json.encode("utf-8")).hexdigest()
        execute(
            """
            INSERT INTO capabilities (id, type, name, description, latest_version_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (capability_id, capability_type, name, description, version_id, now, now),
        )
        execute(
            """
            INSERT INTO capability_versions (
                id, capability_id, version, status, content_hash, rendered_spec, risk_score,
                source_task_id, source_run_id, default_model_selector,
                generation_model, generation_prompt, generation_raw_output, validation_summary, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                version_id,
                capability_id,
                1,
                "pending_approval",
                content_hash,
                rendered_spec_json,
                risk_score,
                source_task_id,
                source_run_id,
                default_model_selector,
                generation_model,
                generation_prompt,
                generation_raw_output,
                dumps_json(validation_summary),
                now,
            ),
        )
        return self.get_capability(capability_id)

    def update_version_status(self, version_id: str, status: str) -> dict[str, Any]:
        execute("UPDATE capability_versions SET status = %s WHERE id = %s", (status, version_id))
        return self.get_version(version_id)

    def record_approval(self, version_id: str, decision: str, approver: str, comment: str) -> None:
        execute(
            """
            INSERT INTO approval_records (id, capability_version_id, decision, approver, comment, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), version_id, decision, approver, comment, utcnow()),
        )

    def _decode(self, row: dict[str, Any]) -> dict[str, Any]:
        decoded = dict(row)
        if "rendered_spec" in decoded:
            decoded["rendered_spec"] = loads_json(decoded["rendered_spec"], {})
        if "validation_summary" in decoded:
            decoded["validation_summary"] = loads_json(decoded["validation_summary"], {})
        return decoded
