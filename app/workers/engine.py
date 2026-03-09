from __future__ import annotations

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from app.agents.code_review import code_review_agent
from app.agents.executor import executor_agent
from app.agents.tester import test_agent
from app.config import settings
from app.db import transaction
from app.orchestrator.task_orchestrator import task_orchestrator
from app.repositories.env_profile_repository import EnvProfileRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.run_repository import RunRepository
from app.repositories.subtask_repository import SubTaskRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.common import dumps_json, utcnow
from app.services.artifact_service import artifact_service
from app.services.event_service import event_service


class WorkerEngine:
    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._active_ids: set[str] = set()
        self._active_lock = threading.Lock()
        self.subtasks = SubTaskRepository()
        self.tasks = TaskRepository()
        self.env_profiles = EnvProfileRepository()
        self.requirements = RequirementRepository()
        self.runs = RunRepository()
        self.pool = ThreadPoolExecutor(max_workers=settings.max_worker_concurrency)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="propagate-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self.pool.shutdown(wait=False, cancel_futures=True)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            available = max(0, settings.max_worker_concurrency - len(self._active_ids))
            if available:
                ready_items = self.subtasks.claim_ready(available)
                for item in ready_items:
                    with self._active_lock:
                        self._active_ids.add(item["id"])
                    future = self.pool.submit(self._run_subtask, item["id"])
                    future.add_done_callback(lambda _, subtask_id=item["id"]: self._release(subtask_id))
            time.sleep(settings.worker_poll_interval_sec)

    def _release(self, subtask_id: str) -> None:
        with self._active_lock:
            self._active_ids.discard(subtask_id)

    def _store_review_result(self, subtask_id: str, review) -> None:
        with transaction() as conn:
            conn.execute(
                """
                INSERT INTO sub_task_review_results (id, sub_task_id, decision, issues_json, summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    subtask_id,
                    "passed" if review.passed else "failed",
                    dumps_json(review.issues),
                    review.summary,
                    utcnow(),
                ),
            )

    def _store_test_result(self, subtask_id: str, test_result) -> None:
        with transaction() as conn:
            conn.execute(
                """
                INSERT INTO sub_task_test_results (id, sub_task_id, passed, command_text, log_excerpt, summary, details_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    subtask_id,
                    int(test_result.passed),
                    test_result.command,
                    test_result.log_excerpt,
                    test_result.summary,
                    dumps_json(test_result.details),
                    utcnow(),
                ),
            )

    def _run_subtask(self, subtask_id: str) -> None:
        subtask = self.subtasks.get_subtask(subtask_id)
        if not subtask:
            return
        task = self.tasks.get_task(subtask["task_id"])
        env_profile = self.env_profiles.get_profile_for_runtime(task["env_profile_id"]) if task else None
        requirement = self.requirements.get_latest(subtask["task_id"])
        if not task or not requirement:
            return
        event_service.publish(task["id"], "subtask.started", f"{subtask['name']} started.", sub_task_id=subtask_id)
        for attempt in range(subtask["retry_count"], subtask["max_retries"] + 1):
            self.subtasks.mark_running(subtask_id)
            run_id = self.runs.start_run(
                task_id=task["id"],
                sub_task_id=subtask_id,
                agent_type=subtask["agent_template"],
                model=(env_profile or {}).get("default_model", settings.default_model),
                input_payload={"attempt": attempt + 1, "subtask": subtask["name"]},
            )
            result = executor_agent.run(task, subtask, requirement, attempt, env_profile)
            path = artifact_service.save_text_artifact(
                task_id=task["id"],
                sub_task_id=subtask_id,
                artifact_type="execution",
                filename=f"execution-attempt-{attempt + 1}.md",
                content=result.content,
                summary=result.summary,
                metadata=result.metadata,
            )
            self.subtasks.update_output_summary(
                subtask_id,
                {
                    "artifact_path": path,
                    "summary": result.summary,
                    "attempt": attempt + 1,
                },
            )
            review = code_review_agent.run(result.content, attempt, env_profile)
            self._store_review_result(subtask_id, review)
            if not review.passed:
                event_service.publish(
                    task["id"],
                    "subtask.review.failed",
                    review.summary,
                    level="warn",
                    sub_task_id=subtask_id,
                )
                self.runs.finish_run(run_id, "RETRY", output_payload={"review": review.summary})
                if attempt >= subtask["max_retries"]:
                    self.subtasks.mark_needs_human_review(
                        subtask_id,
                        attempt + 1,
                        {"reason": review.summary},
                    )
                    event_service.publish(
                        task["id"],
                        "subtask.review.failed",
                        review.summary,
                        level="error",
                        sub_task_id=subtask_id,
                    )
                    task_orchestrator.finalize_task_if_done(task["id"])
                    return
                self.subtasks.mark_retry_pending(subtask_id, attempt + 1)
                event_service.publish(
                    task["id"],
                    "subtask.retrying",
                    f"{subtask['name']} retrying after review failure.",
                    level="warn",
                    sub_task_id=subtask_id,
                    payload={"attempt": attempt + 2},
                )
                subtask = self.subtasks.get_subtask(subtask_id)
                continue
            test_result = test_agent.run(subtask, result.content, attempt, env_profile)
            self._store_test_result(subtask_id, test_result)
            if not test_result.passed:
                event_service.publish(
                    task["id"],
                    "subtask.test.failed",
                    test_result.summary,
                    level="warn",
                    sub_task_id=subtask_id,
                )
                self.runs.finish_run(run_id, "RETRY", output_payload={"test": test_result.summary})
                if attempt >= subtask["max_retries"]:
                    self.subtasks.mark_needs_human_review(
                        subtask_id,
                        attempt + 1,
                        {"reason": test_result.summary},
                    )
                    event_service.publish(
                        task["id"],
                        "subtask.test.failed",
                        test_result.summary,
                        level="error",
                        sub_task_id=subtask_id,
                    )
                    task_orchestrator.finalize_task_if_done(task["id"])
                    return
                self.subtasks.mark_retry_pending(subtask_id, attempt + 1)
                event_service.publish(
                    task["id"],
                    "subtask.retrying",
                    f"{subtask['name']} retrying after test failure.",
                    level="warn",
                    sub_task_id=subtask_id,
                    payload={"attempt": attempt + 2},
                )
                subtask = self.subtasks.get_subtask(subtask_id)
                continue
            self.runs.finish_run(run_id, "COMPLETED", output_payload={"summary": result.summary})
            self.subtasks.mark_completed(
                subtask_id,
                {
                    "artifact_path": path,
                    "summary": result.summary,
                    "review_summary": review.summary,
                    "test_summary": test_result.summary,
                },
            )
            event_service.publish(
                task["id"],
                "subtask.completed",
                f"{subtask['name']} completed successfully.",
                sub_task_id=subtask_id,
            )
            task_orchestrator.refresh_ready_subtasks(task["id"])
            task_orchestrator.finalize_task_if_done(task["id"])
            return


worker_engine = WorkerEngine()
