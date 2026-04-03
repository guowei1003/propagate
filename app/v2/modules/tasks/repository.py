from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.v2.core.db import dumps_json, fetch_all, fetch_one, execute, loads_json
from app.v2.core.errors import NotFoundError


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


class TaskRepositoryV2:
    def create_task(self, *, title: str, prompt: str, env_profile_id: str, model_overrides: dict[str, str]) -> dict[str, Any]:
        task_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        now = utcnow()
        execute(
            """
            INSERT INTO tasks (id, title, prompt, status, current_phase, env_profile_id, model_overrides_json, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                task_id,
                title,
                prompt,
                "CREATED",
                "REQUIREMENT_ANALYZING",
                env_profile_id,
                dumps_json(model_overrides),
                now,
                now,
            ),
        )
        execute(
            """
            INSERT INTO runs (id, task_id, status, current_phase, env_profile_id, model_overrides_json, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (run_id, task_id, "CREATED", "REQUIREMENT_ANALYZING", env_profile_id, dumps_json(model_overrides), now, now),
        )
        return self.get_task(task_id)

    def list_tasks(self) -> list[dict[str, Any]]:
        rows = fetch_all(
            """
            SELECT t.*, r.id AS run_id, r.status AS run_status, r.current_phase AS run_phase
            FROM tasks t
            LEFT JOIN runs r ON r.task_id = t.id
            ORDER BY t.created_at DESC
            """
        )
        return [self._decode(row) for row in rows]

    def get_task(self, task_id: str) -> dict[str, Any]:
        row = fetch_one("SELECT * FROM tasks WHERE id = %s", (task_id,))
        if not row:
            raise NotFoundError(f"Task {task_id} not found.")
        task = self._decode(row)
        run = fetch_one("SELECT * FROM runs WHERE task_id = %s ORDER BY created_at DESC LIMIT 1", (task_id,))
        requirement = fetch_one(
            "SELECT * FROM task_requirements WHERE task_id = %s ORDER BY version DESC LIMIT 1",
            (task_id,),
        )
        clarification_rounds = fetch_all(
            "SELECT * FROM clarification_rounds WHERE task_id = %s ORDER BY created_at ASC",
            (task_id,),
        )
        subtasks = fetch_all(
            "SELECT * FROM sub_tasks WHERE task_id = %s ORDER BY sequence_no ASC",
            (task_id,),
        )
        events = fetch_all(
            "SELECT * FROM task_events WHERE task_id = %s ORDER BY created_at ASC",
            (task_id,),
        )
        env_profile = fetch_one(
            """
            SELECT id, name, provider_type, default_model, review_model, test_model,
                   capability_generation_model, report_model
            FROM env_profiles
            WHERE id = %s
            """,
            (task["env_profile_id"],),
        )
        dependencies = fetch_all(
            "SELECT * FROM sub_task_dependencies WHERE task_id = %s ORDER BY created_at ASC",
            (task_id,),
        )
        task["run"] = self._decode(run) if run else None
        task["requirement"] = self._decode(requirement) if requirement else None
        task["env_profile"] = self._decode(env_profile) if env_profile else None
        task["clarification_rounds"] = [self._decode(item) for item in clarification_rounds]
        task["subtasks"] = [self._decode(item) for item in subtasks]
        task["dependencies"] = [self._decode(item) for item in dependencies]
        task["events"] = [self._decode(item) for item in events]
        return task

    def get_run(self, run_id: str) -> dict[str, Any]:
        row = fetch_one("SELECT * FROM runs WHERE id = %s", (run_id,))
        if not row:
            raise NotFoundError(f"Run {run_id} not found.")
        return self._decode(row)

    def save_requirement(self, task_id: str, requirement: dict[str, Any]) -> None:
        latest = fetch_one("SELECT COALESCE(MAX(version), 0) AS version FROM task_requirements WHERE task_id = %s", (task_id,))
        version = int((latest or {}).get("version") or 0) + 1
        execute(
            """
            INSERT INTO task_requirements (
                id, task_id, version, goal, scope, inputs_json, outputs_json, constraints_json,
                acceptance_json, missing_info_json, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(uuid.uuid4()),
                task_id,
                version,
                requirement["goal"],
                requirement["scope"],
                dumps_json(requirement["inputs"]),
                dumps_json(requirement["outputs"]),
                dumps_json(requirement["constraints"]),
                dumps_json(requirement["acceptance"]),
                dumps_json(requirement["missing_info"]),
                utcnow(),
            ),
        )

    def create_clarification_round(self, task_id: str, questions: list[dict[str, str]]) -> dict[str, Any]:
        round_id = str(uuid.uuid4())
        execute(
            """
            INSERT INTO clarification_rounds (id, task_id, status, questions_json, answers_json, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (round_id, task_id, "pending", dumps_json(questions), dumps_json({}), utcnow()),
        )
        return self.get_clarification_round(round_id)

    def get_clarification_round(self, round_id: str) -> dict[str, Any]:
        row = fetch_one("SELECT * FROM clarification_rounds WHERE id = %s", (round_id,))
        if not row:
            raise NotFoundError(f"Clarification round {round_id} not found.")
        return self._decode(row)

    def answer_clarification_round(self, round_id: str, answers: dict[str, str]) -> dict[str, Any]:
        execute(
            """
            UPDATE clarification_rounds
            SET status = %s, answers_json = %s, answered_at = %s
            WHERE id = %s
            """,
            ("answered", dumps_json(answers), utcnow(), round_id),
        )
        return self.get_clarification_round(round_id)

    def replace_subtasks(self, task_id: str, run_id: str, subtasks: list[dict[str, Any]]) -> None:
        execute("DELETE FROM sub_tasks WHERE task_id = %s", (task_id,))
        execute("DELETE FROM sub_task_dependencies WHERE task_id = %s", (task_id,))
        for index, item in enumerate(subtasks):
            execute(
                """
                INSERT INTO sub_tasks (
                    id, task_id, run_id, name, description, category, status, sequence_no, priority,
                    capability_bindings_json, acceptance_json, input_context_json, output_summary_json, retry_count, max_retries,
                    timeout_sec, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    item["id"],
                    task_id,
                    run_id,
                    item["name"],
                    item["description"],
                    item["category"],
                    item["status"],
                    index,
                    item["priority"],
                    dumps_json(item["capability_bindings"]),
                    dumps_json(item["acceptance"]),
                    dumps_json(item["input_context"]),
                    dumps_json(
                        {
                            "review_policy": item.get("review_policy", {}),
                            "test_command": item.get("test_command", ""),
                        }
                    ),
                    0,
                    item["max_retries"],
                    item["timeout_sec"],
                    utcnow(),
                    utcnow(),
                ),
            )
        for dependency in subtasks:
            for blocker_id in dependency.get("depends_on_ids", []):
                execute(
                    """
                    INSERT INTO sub_task_dependencies (
                        id, task_id, from_sub_task_id, to_sub_task_id, created_at
                    ) VALUES (%s, %s, %s, %s, %s)
                    """,
                    (str(uuid.uuid4()), task_id, blocker_id, dependency["id"], utcnow()),
                )

    def update_task_status(self, task_id: str, *, status: str, phase: str) -> None:
        execute(
            "UPDATE tasks SET status = %s, current_phase = %s, updated_at = %s WHERE id = %s",
            (status, phase, utcnow(), task_id),
        )

    def update_run_status(self, run_id: str, *, status: str, phase: str) -> None:
        execute(
            "UPDATE runs SET status = %s, current_phase = %s, updated_at = %s WHERE id = %s",
            (status, phase, utcnow(), run_id),
        )

    def list_run_subtasks(self, run_id: str) -> list[dict[str, Any]]:
        rows = fetch_all("SELECT * FROM sub_tasks WHERE run_id = %s ORDER BY sequence_no ASC", (run_id,))
        return [self._decode(row) for row in rows]

    def list_dependencies(self, task_id: str) -> list[dict[str, Any]]:
        rows = fetch_all(
            "SELECT * FROM sub_task_dependencies WHERE task_id = %s ORDER BY created_at ASC",
            (task_id,),
        )
        return [self._decode(row) for row in rows]

    def mark_subtask_blocked(self, subtask_id: str, reason: str) -> None:
        self.update_subtask(subtask_id, status="BLOCKED_BY_DEPENDENCY", output_summary_json={"blocked_reason": reason})

    def mark_dependents_blocked(self, task_id: str, subtask_ids: list[str], reason: str) -> None:
        for subtask_id in subtask_ids:
            self.mark_subtask_blocked(subtask_id, reason)

    def update_subtask(self, subtask_id: str, **fields: Any) -> None:
        if not fields:
            return
        columns: list[str] = []
        params: list[Any] = []
        mapping = {
            "status": "status",
            "retry_count": "retry_count",
            "output_summary_json": "output_summary_json",
            "started_at": "started_at",
            "completed_at": "completed_at",
        }
        for key, value in fields.items():
            column = mapping[key]
            columns.append(f"{column} = %s")
            if column.endswith("_json"):
                params.append(dumps_json(value))
            else:
                params.append(value)
        columns.append("updated_at = %s")
        params.append(utcnow())
        params.append(subtask_id)
        execute(f"UPDATE sub_tasks SET {', '.join(columns)} WHERE id = %s", tuple(params))

    def append_event(
        self,
        *,
        task_id: str,
        run_id: str,
        event_type: str,
        message: str,
        level: str = "info",
        sub_task_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        execute(
            """
            INSERT INTO task_events (id, task_id, run_id, sub_task_id, event_type, level, message, payload_json, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), task_id, run_id, sub_task_id, event_type, level, message, dumps_json(payload or {}), utcnow()),
        )

    def list_run_events(self, run_id: str) -> list[dict[str, Any]]:
        rows = fetch_all("SELECT * FROM task_events WHERE run_id = %s ORDER BY created_at ASC", (run_id,))
        return [self._decode(row) for row in rows]

    def save_report(self, task_id: str, run_id: str, report_markdown: str, summary: dict[str, Any]) -> None:
        existing = fetch_one("SELECT id FROM task_reports WHERE run_id = %s", (run_id,))
        if existing:
            execute(
                "UPDATE task_reports SET report_markdown = %s, summary_json = %s, created_at = %s WHERE run_id = %s",
                (report_markdown, dumps_json(summary), utcnow(), run_id),
            )
            return
        execute(
            """
            INSERT INTO task_reports (id, task_id, run_id, report_markdown, summary_json, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), task_id, run_id, report_markdown, dumps_json(summary), utcnow()),
        )

    def get_report(self, run_id: str) -> dict[str, Any] | None:
        row = fetch_one("SELECT * FROM task_reports WHERE run_id = %s", (run_id,))
        return self._decode(row) if row else None

    def save_review_result(self, sub_task_id: str, decision: str, summary: str, issues: list[str]) -> None:
        execute(
            """
            INSERT INTO sub_task_review_results (id, sub_task_id, decision, issues_json, summary, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), sub_task_id, decision, dumps_json(issues), summary, utcnow()),
        )

    def save_test_result(self, sub_task_id: str, passed: bool, command_text: str, log_excerpt: str, summary: str) -> None:
        execute(
            """
            INSERT INTO sub_task_test_results (id, sub_task_id, passed, command_text, log_excerpt, summary, details_json, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), sub_task_id, passed, command_text, log_excerpt, summary, dumps_json({}), utcnow()),
        )

    def save_artifact(self, task_id: str, run_id: str, sub_task_id: str | None, artifact_type: str, path: str, summary: str, metadata: dict[str, Any]) -> None:
        execute(
            """
            INSERT INTO artifacts (id, task_id, run_id, sub_task_id, artifact_type, path, summary, metadata_json, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), task_id, run_id, sub_task_id, artifact_type, path, summary, dumps_json(metadata), utcnow()),
        )

    def list_artifacts(self, run_id: str) -> list[dict[str, Any]]:
        rows = fetch_all("SELECT * FROM artifacts WHERE run_id = %s ORDER BY created_at ASC", (run_id,))
        return [self._decode(row) for row in rows]

    def save_execution_evidence(self, run_id: str, task_id: str, sub_task_id: str, evidence: dict[str, Any]) -> None:
        execute(
            """
            INSERT INTO execution_evidence (
                id, run_id, task_id, sub_task_id, command, exit_code, stdout_path, stderr_path,
                output_files_json, file_hashes_json, container_metadata_json, started_at, completed_at, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(uuid.uuid4()),
                run_id,
                task_id,
                sub_task_id,
                evidence["command"],
                evidence["exit_code"],
                evidence["stdout_path"],
                evidence["stderr_path"],
                dumps_json(evidence["output_files"]),
                dumps_json(evidence["file_hashes"]),
                dumps_json(evidence["container_metadata"]),
                evidence["started_at"],
                evidence["completed_at"],
                utcnow(),
            ),
        )

    def list_execution_evidence(self, run_id: str) -> list[dict[str, Any]]:
        rows = fetch_all("SELECT * FROM execution_evidence WHERE run_id = %s ORDER BY created_at ASC", (run_id,))
        return [self._decode(row) for row in rows]

    def _decode(self, row: dict[str, Any] | None) -> dict[str, Any] | None:
        if row is None:
            return None
        decoded = dict(row)
        for key in list(decoded.keys()):
            if key.endswith("_json"):
                decoded[key[:-5]] = loads_json(decoded.pop(key), {})
        return decoded
