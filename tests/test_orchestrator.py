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

    def test_runtime_isolation_context_created_for_subtasks(self) -> None:
        task_id = task_orchestrator.create_task(
            title="Build site",
            prompt="创建一个网站，包含前后端和任务调度",
            env_profile_id=self.profile["id"],
        )
        pending = ClarificationRepository().get_pending_round(task_id)
        self.assertIsNotNone(pending)
        task_orchestrator.submit_clarification_answers(
            task_id,
            pending["id"],
            {
                "deliverable": "可运行的网站代码",
                "acceptance": "核心流程可访问、日志可追踪、报告生成",
                "scope": "包括登录、任务创建、任务详情和事件流展示页面",
                "target_users": "中小团队运营人员",
                "core_features": "登录、任务创建、进度追踪",
                "style_preferences": "简洁商务风格",
            },
        )
        subtasks = SubTaskRepository().list_by_task(task_id)
        self.assertGreaterEqual(len(subtasks), 2)
        for subtask in subtasks:
            runtime = subtask["input_context"].get("runtime")
            self.assertIsNotNone(runtime)
            self.assertTrue(Path(runtime["workspace_path"]).exists())
            self.assertTrue(Path(runtime["manifest_path"]).exists())
            self.assertGreaterEqual(len(runtime["skill_files"]), 1)
            self.assertTrue(subtask["agent_template"].startswith("tmp_"))

    def test_disable_auto_sub_agents_keeps_static_templates(self) -> None:
        profile_id = self.env_repo.create_profile(
            name="No Auto Agent",
            provider_type="demo",
            api_base_url="",
            api_key="",
            default_model="demo-heuristic",
            review_model="demo-review",
            test_model="demo-test",
            temperature=0.2,
            max_concurrency=1,
            default_timeout_sec=300,
            max_retries=1,
            enable_auto_sub_agents=False,
            enable_docker_sandbox=False,
        )
        task_id = task_orchestrator.create_task(
            title="Static template",
            prompt="实现一个后端任务编排系统",
            env_profile_id=profile_id,
        )
        pending = ClarificationRepository().get_pending_round(task_id)
        self.assertIsNotNone(pending)
        task_orchestrator.submit_clarification_answers(
            task_id,
            pending["id"],
            {"deliverable": "后端代码", "acceptance": "接口可用并产生报告", "scope": "任务编排、子任务管理和报告生成"},
        )
        subtasks = SubTaskRepository().list_by_task(task_id)
        self.assertGreaterEqual(len(subtasks), 1)
        self.assertFalse(any(item["agent_template"].startswith("tmp_") for item in subtasks))

    def test_auto_title_generated_from_requirement_when_title_missing(self) -> None:
        task_id = task_orchestrator.create_task(
            title=None,
            prompt="实现一个任务管理网站，支持看板、筛选和实时日志",
            env_profile_id=self.profile["id"],
        )
        pending = ClarificationRepository().get_pending_round(task_id)
        self.assertIsNotNone(pending)
        task_orchestrator.submit_clarification_answers(
            task_id,
            pending["id"],
            {
                "deliverable": "任务管理网站代码",
                "acceptance": "可创建任务并查看实时日志",
                "scope": "任务看板、筛选、实时日志三大功能",
                "target_users": "项目经理与开发",
                "core_features": "任务看板、筛选、日志",
                "style_preferences": "极简风格",
            },
        )
        task = TaskRepository().get_task(task_id)
        self.assertEqual(task["title"], "任务管理网站代码")
        self.assertEqual(int(task["title_auto_generated"]), 1)

    def test_manual_title_is_not_overwritten(self) -> None:
        task_id = task_orchestrator.create_task(
            title="固定标题",
            prompt="实现一个任务管理网站，支持看板、筛选和实时日志",
            env_profile_id=self.profile["id"],
        )
        pending = ClarificationRepository().get_pending_round(task_id)
        self.assertIsNotNone(pending)
        task_orchestrator.submit_clarification_answers(
            task_id,
            pending["id"],
            {
                "deliverable": "任务管理网站代码",
                "acceptance": "可创建任务并查看实时日志",
                "scope": "任务看板、筛选、实时日志三大功能",
                "target_users": "项目经理与开发",
                "core_features": "任务看板、筛选、日志",
                "style_preferences": "极简风格",
            },
        )
        task = TaskRepository().get_task(task_id)
        self.assertEqual(task["title"], "固定标题")
        self.assertEqual(int(task["title_auto_generated"]), 0)


if __name__ == "__main__":
    unittest.main()
