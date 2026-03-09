from __future__ import annotations

import unittest
from pathlib import Path

from app.config import BASE_DIR
from app.db import init_db
from app.orchestrator.task_orchestrator import task_orchestrator
from app.repositories.clarification_repository import ClarificationRepository
from app.repositories.env_profile_repository import EnvProfileRepository
from app.repositories.subtask_repository import SubTaskRepository
from app.repositories.task_repository import TaskRepository


class OrchestratorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        db_path = BASE_DIR / "data" / "propagate.db"
        if db_path.exists():
            db_path.unlink()
        artifacts_root = BASE_DIR / "data" / "artifacts"
        if artifacts_root.exists():
            for item in sorted(artifacts_root.rglob("*"), reverse=True):
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    item.rmdir()
        init_db()
        self.env_repo = EnvProfileRepository()
        self.env_repo.seed_default_profile()
        self.profile = self.env_repo.get_default_profile()

    def test_task_enters_clarification_when_missing_info(self) -> None:
        task_id = task_orchestrator.create_task(
            title="Need details",
            prompt="做一个系统",
            env_profile_id=self.profile["id"],
        )
        task = TaskRepository().get_task(task_id)
        self.assertEqual(task["status"], "WAITING_USER_INPUT")
        self.assertIsNotNone(ClarificationRepository().get_pending_round(task_id))

    def test_task_decomposes_after_clarification(self) -> None:
        task_id = task_orchestrator.create_task(
            title="Build system",
            prompt="实现一个有 UI 和后端 agent 编排的系统",
            env_profile_id=self.profile["id"],
        )
        pending = ClarificationRepository().get_pending_round(task_id)
        self.assertIsNotNone(pending)
        task_orchestrator.submit_clarification_answers(
            task_id,
            pending["id"],
            {"deliverable": "完整产品", "acceptance": "页面可用、日志可见、报告生成"},
        )
        subtasks = SubTaskRepository().list_by_task(task_id)
        self.assertGreaterEqual(len(subtasks), 2)


if __name__ == "__main__":
    unittest.main()

