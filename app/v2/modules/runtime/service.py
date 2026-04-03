from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tarfile
from datetime import UTC, datetime
from pathlib import Path

from app.v2.core.config import v2_settings
from app.v2.core.errors import ConflictError
from app.v2.core.models import CapabilityVersion, ExecutionEvidence
from app.v2.modules.capabilities.repository import CapabilityRepository
from app.v2.modules.env_profiles.service import env_profile_service
from app.v2.modules.env_profiles.model_routing import resolve_model_for_stage
from app.v2.modules.runtime.guardrails import GuardrailViolation, preflight_guard
from app.v2.modules.runtime.review_and_test import evaluate_review, evaluate_test
from app.v2.modules.runtime.state_machine import derive_run_status_and_phase
from app.v2.modules.tasks.dependency_resolver import block_dependents, compute_ready_subtasks
from app.v2.modules.tasks.repository import TaskRepositoryV2


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


class RuntimeService:
    def __init__(self) -> None:
        self.tasks = TaskRepositoryV2()
        self.capabilities = CapabilityRepository()

    def _runtime_dir(self, run_id: str) -> Path:
        return v2_settings.runtime_root / run_id

    def _prepare_workspace(self, run_id: str, subtask_id: str) -> Path:
        workspace = self._runtime_dir(run_id) / subtask_id
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def _resolve_capabilities(self, bindings: list[dict]) -> tuple[dict, dict]:
        agent = {}
        skill = {}
        for item in bindings:
            capability = self.capabilities.get_capability(item["capability_id"])
            if item["type"] == "agent":
                agent = capability
            elif item["type"] == "skill":
                skill = capability
        return agent, skill

    def _docker_command(self, workspace: Path, command: str) -> list[str]:
        return [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "-v",
            f"{workspace}:/workspace",
            "-w",
            "/workspace",
            "python:3.11-slim",
            "sh",
            "-lc",
            command,
        ]

    def _collect_requested_paths(self, command: str) -> list[str]:
        paths = ["/workspace/stdout.log", "/workspace/stderr.log", "/workspace/result.txt"]
        for token in command.split():
            if token.startswith("/workspace/"):
                paths.append(token)
        return sorted(set(paths))

    def _collect_output_files(self, workspace: Path) -> tuple[list[str], dict[str, str]]:
        output_files: list[str] = []
        file_hashes: dict[str, str] = {}
        for item in workspace.rglob("*"):
            if not item.is_file():
                continue
            rel = item.relative_to(workspace)
            output_files.append(str(rel))
            file_hashes[str(rel)] = f"sha256:{hashlib.sha256(item.read_bytes()).hexdigest()}"
        return sorted(output_files), file_hashes

    def _run_test_command(self, workspace: Path, test_command: str, timeout_sec: int) -> tuple[int, str, str]:
        if not test_command.strip():
            return 0, "fallback-test", ""
        docker_cmd = self._docker_command(workspace, test_command)
        try:
            result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout_sec)
            return result.returncode, result.stdout, result.stderr
        except FileNotFoundError as exc:
            return 127, "", str(exc)
        except subprocess.TimeoutExpired as exc:
            return 124, exc.stdout or "", exc.stderr or "Test command timed out."

    def _run_subtask_once(self, run: dict, task: dict, subtask: dict) -> tuple[ExecutionEvidence, str]:
        workspace = self._prepare_workspace(run["id"], subtask["id"])
        bindings = subtask["capability_bindings"]
        agent_cap, skill_cap = self._resolve_capabilities(bindings)
        if not agent_cap or not skill_cap:
            raise ConflictError("Subtask capability bindings are incomplete.")
        if agent_cap["status"] != "approved" or skill_cap["status"] != "approved":
            raise ConflictError("Subtask requires approved agent and skill capabilities before execution.")

        command = (
            skill_cap["rendered_spec"].get("allowed_commands") or ["printf 'no command configured\\n' > result.txt"]
        )[0]
        started_at = utcnow()
        stdout_path = workspace / "stdout.log"
        stderr_path = workspace / "stderr.log"
        manifest_path = workspace / "execution-manifest.json"
        env_profile = env_profile_service.get_profile_for_runtime(run["env_profile_id"])
        agent_version = CapabilityVersion(
            capability_id=agent_cap["id"],
            version=int(agent_cap["version"]),
            status=agent_cap["status"],
            content_hash=agent_cap["content_hash"],
            rendered_spec=json.dumps(agent_cap["rendered_spec"], ensure_ascii=False),
            risk_score=int(agent_cap["risk_score"]),
            source_task_id=agent_cap.get("source_task_id") or "",
            source_run_id=agent_cap.get("source_run_id") or "",
            default_model_selector=agent_cap.get("default_model_selector") or "",
        )
        selected_model = resolve_model_for_stage(
            "execution",
            env_profile,
            agent_version,
            run.get("model_overrides", {}),
        )
        preflight_guard(
            command=command,
            allowed_commands=skill_cap["rendered_spec"].get("allowed_commands") or [],
            allowed_file_scope=skill_cap["rendered_spec"].get("allowed_file_scope") or ["/workspace"],
            requested_paths=self._collect_requested_paths(command),
        )
        manifest_path.write_text(
            json.dumps(
                {
                    "task_id": task["id"],
                    "run_id": run["id"],
                    "subtask_id": subtask["id"],
                    "command": command,
                    "selected_model": selected_model,
                    "capabilities": bindings,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        docker_cmd = self._docker_command(workspace, command)
        try:
            result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=int(subtask["timeout_sec"]))
            stdout_text = result.stdout
            stderr_text = result.stderr
            exit_code = result.returncode
        except FileNotFoundError as exc:
            stdout_text = ""
            stderr_text = str(exc)
            exit_code = 127
        except subprocess.TimeoutExpired as exc:
            stdout_text = exc.stdout or ""
            stderr_text = exc.stderr or "Execution timed out."
            exit_code = 124
        stdout_path.write_text(stdout_text, encoding="utf-8")
        stderr_path.write_text(stderr_text, encoding="utf-8")
        output_files, file_hashes = self._collect_output_files(workspace)
        completed_at = utcnow()
        evidence = ExecutionEvidence(
            run_id=run["id"],
            sub_task_id=subtask["id"],
            command=command,
            exit_code=exit_code,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            output_files=output_files,
            file_hashes=file_hashes,
            container_metadata={"engine": "docker", "image": "python:3.11-slim"},
            started_at=started_at,
            completed_at=completed_at,
        )
        return evidence, selected_model

    def _refresh_ready_subtasks(self, task_id: str, run_id: str) -> list[dict]:
        subtasks = self.tasks.list_run_subtasks(run_id)
        dependencies = self.tasks.list_dependencies(task_id)
        ready_ids = set(compute_ready_subtasks(subtasks, dependencies))
        refreshed: list[dict] = []
        for item in subtasks:
            if item["id"] in ready_ids and item["status"] != "READY":
                self.tasks.update_subtask(item["id"], status="READY")
                item["status"] = "READY"
            refreshed.append(item)
        return refreshed

    def _block_dependents(self, task: dict, run_id: str, failed_subtask_id: str, reason: str) -> None:
        subtasks = self.tasks.list_run_subtasks(run_id)
        dependencies = self.tasks.list_dependencies(task["id"])
        blocked_ids = block_dependents(subtasks, dependencies, failed_subtask_id=failed_subtask_id)
        if not blocked_ids:
            return
        self.tasks.mark_dependents_blocked(task["id"], blocked_ids, reason)
        self.tasks.append_event(
            task_id=task["id"],
            run_id=run_id,
            event_type="subtask.dependents.blocked",
            level="warn",
            message=f"{len(blocked_ids)} downstream subtasks blocked.",
            payload={"blocked_ids": blocked_ids, "reason": reason},
        )

    def resume_run(self, run_id: str) -> dict:
        run = self.tasks.get_run(run_id)
        task = self.tasks.get_task(run["task_id"])
        self.tasks.update_run_status(run_id, status="RUNNING", phase="SUBTASK_RUNNING")
        self.tasks.update_task_status(task["id"], status="RUNNING", phase="SUBTASK_RUNNING")
        self.tasks.append_event(task_id=task["id"], run_id=run_id, event_type="run.resumed", message="Run resumed.")
        all_success = True
        while True:
            subtasks = self._refresh_ready_subtasks(task["id"], run_id)
            ready_subtasks = [item for item in subtasks if item["status"] == "READY"]
            if not ready_subtasks:
                break
            for subtask in ready_subtasks:
                self.tasks.update_subtask(subtask["id"], status="RUNNING", started_at=utcnow())
                self.tasks.append_event(
                    task_id=task["id"],
                    run_id=run_id,
                    sub_task_id=subtask["id"],
                    event_type="subtask.started",
                    message=f"{subtask['name']} started.",
                )
                success = False
                selected_model = ""
                try:
                    for attempt in range(int(subtask["retry_count"]), int(subtask["max_retries"]) + 1):
                        evidence, selected_model = self._run_subtask_once(run, task, subtask)
                        self.tasks.save_execution_evidence(
                            run_id,
                            task["id"],
                            subtask["id"],
                            {
                                "command": evidence.command,
                                "exit_code": evidence.exit_code,
                                "stdout_path": evidence.stdout_path,
                                "stderr_path": evidence.stderr_path,
                                "output_files": evidence.output_files,
                                "file_hashes": evidence.file_hashes,
                                "container_metadata": evidence.container_metadata,
                                "started_at": evidence.started_at,
                                "completed_at": evidence.completed_at,
                            },
                        )
                        self.tasks.save_artifact(
                            task["id"],
                            run_id,
                            subtask["id"],
                            "execution_evidence",
                            evidence.stdout_path,
                            f"Execution attempt {attempt + 1}",
                            {"selected_model": selected_model, "exit_code": evidence.exit_code},
                        )
                        review = evaluate_review(
                            exit_code=evidence.exit_code,
                            stdout_text=Path(evidence.stdout_path).read_text(encoding="utf-8"),
                            stderr_text=Path(evidence.stderr_path).read_text(encoding="utf-8"),
                            output_files=evidence.output_files,
                            review_policy=subtask.get("output_summary", {}).get("review_policy", {}),
                        )
                        self.tasks.save_review_result(
                            subtask["id"],
                            "passed" if review.passed else "failed",
                            review.summary,
                            review.issues,
                        )
                        if not review.passed:
                            self.tasks.append_event(
                                task_id=task["id"],
                                run_id=run_id,
                                sub_task_id=subtask["id"],
                                event_type="subtask.review.failed",
                                level="warn",
                                message=review.summary,
                            )
                        test_command = subtask.get("output_summary", {}).get("test_command", "")
                        test_exit_code, test_stdout, test_stderr = self._run_test_command(
                            Path(evidence.stdout_path).parent,
                            test_command,
                            int(subtask["timeout_sec"]),
                        )
                        test = evaluate_test(
                            exit_code=test_exit_code,
                            stdout_text=test_stdout,
                            stderr_text=test_stderr,
                            test_command=test_command,
                        )
                        self.tasks.save_test_result(
                            subtask["id"],
                            test.passed,
                            test_command or evidence.command,
                            test.log_excerpt,
                            test.summary,
                        )
                        if review.passed and test.passed:
                            success = True
                            self.tasks.update_subtask(
                                subtask["id"],
                                status="COMPLETED",
                                completed_at=utcnow(),
                                output_summary_json={
                                    **subtask.get("output_summary", {}),
                                    "selected_model": selected_model,
                                    "exit_code": evidence.exit_code,
                                    "output_files": evidence.output_files,
                                },
                            )
                            self.tasks.append_event(
                                task_id=task["id"],
                                run_id=run_id,
                                sub_task_id=subtask["id"],
                                event_type="subtask.completed",
                                message=f"{subtask['name']} completed.",
                                payload={"selected_model": selected_model},
                            )
                            break
                        if attempt >= int(subtask["max_retries"]):
                            self.tasks.update_subtask(
                                subtask["id"],
                                status="NEEDS_HUMAN_REVIEW",
                                retry_count=attempt + 1,
                                output_summary_json={
                                    **subtask.get("output_summary", {}),
                                    "selected_model": selected_model,
                                    "exit_code": evidence.exit_code,
                                },
                            )
                            self._block_dependents(task, run_id, subtask["id"], f"{subtask['name']} failed after retries.")
                            self.tasks.append_event(
                                task_id=task["id"],
                                run_id=run_id,
                                sub_task_id=subtask["id"],
                                event_type="subtask.failed",
                                level="error",
                                message=f"{subtask['name']} requires human review.",
                                payload={"selected_model": selected_model, "exit_code": evidence.exit_code},
                            )
                            break
                        self.tasks.update_subtask(subtask["id"], status="RETRY_PENDING", retry_count=attempt + 1)
                        self.tasks.append_event(
                            task_id=task["id"],
                            run_id=run_id,
                            sub_task_id=subtask["id"],
                            event_type="subtask.retrying",
                            level="warn",
                            message=f"{subtask['name']} retrying.",
                            payload={"attempt": attempt + 2},
                        )
                except GuardrailViolation as exc:
                    success = False
                    self.tasks.update_subtask(
                        subtask["id"],
                        status="NEEDS_HUMAN_REVIEW",
                        output_summary_json={**subtask.get("output_summary", {}), "guardrail": str(exc)},
                    )
                    self._block_dependents(task, run_id, subtask["id"], str(exc))
                    self.tasks.append_event(
                        task_id=task["id"],
                        run_id=run_id,
                        sub_task_id=subtask["id"],
                        event_type="subtask.guardrail.blocked",
                        level="error",
                        message=str(exc),
                    )
                all_success = all_success and success
        evidence_rows = self.tasks.list_execution_evidence(run_id)
        report_markdown = "\n".join(
            [
                f"# Run {run_id}",
                "",
                f"- Task: {task['title']}",
                f"- Status: {'COMPLETED' if all_success else 'PARTIAL_SUCCESS'}",
                f"- Evidence count: {len(evidence_rows)}",
            ]
        )
        self.tasks.save_report(
            task["id"],
            run_id,
            report_markdown,
            {"status": "COMPLETED" if all_success else "PARTIAL_SUCCESS", "evidence_count": len(evidence_rows)},
        )
        self.tasks.save_artifact(task["id"], run_id, None, "report", f"run:{run_id}:report", "Run report", {})
        terminal_subtasks = self.tasks.list_run_subtasks(run_id)
        final_status, final_phase = derive_run_status_and_phase(terminal_subtasks, all_success=all_success)
        self.tasks.update_run_status(run_id, status=final_status, phase=final_phase)
        self.tasks.update_task_status(task["id"], status=final_status, phase=final_phase)
        if final_status == "RUNNING":
            self.tasks.append_event(
                task_id=task["id"],
                run_id=run_id,
                event_type="run.waiting",
                level="warn",
                message="No READY subtasks remain; waiting for human action or dependency resolution.",
            )
        self.tasks.append_event(task_id=task["id"], run_id=run_id, event_type="task.report.generated", message="Run report generated.")
        return self.tasks.get_task(task["id"])

    def get_run_artifacts(self, run_id: str) -> dict:
        return {
            "artifacts": self.tasks.list_artifacts(run_id),
            "evidence": self.tasks.list_execution_evidence(run_id),
            "report": self.tasks.get_report(run_id),
        }

    def stream_events(self, run_id: str) -> list[dict]:
        return self.tasks.list_run_events(run_id)


runtime_service = RuntimeService()
