from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

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
        self.profile_id = self.env_repo.create_profile(
            name="OpenAI Mock",
            provider_type="openai_compatible",
            api_base_url="https://example.com/v1",
            api_key="test-key",
            default_model="gpt-mock",
            review_model="gpt-mock-review",
            test_model="gpt-mock-test",
            temperature=0.2,
            max_concurrency=2,
            default_timeout_sec=300,
            max_retries=1,
            enable_auto_sub_agents=True,
            enable_docker_sandbox=False,
        )
        self.profile = self.env_repo.get_profile(self.profile_id)

    def _answer_all_pending_questions(self, task_id: str, default_answer: str = "已确认") -> None:
        pending = ClarificationRepository().get_pending_round(task_id)
        self.assertIsNotNone(pending)
        answers = {item["key"]: f"{default_answer}:{item['key']}" for item in pending["questions"] if item.get("key")}
        self.assertGreater(len(answers), 0)
        task_orchestrator.submit_clarification_answers(task_id, pending["id"], answers)

    def _mock_llm_missing_info(self, mock_generate) -> None:
        mock_generate.return_value = {
            "provider_type": "openai_compatible",
            "model": "mock-model",
            "content": (
                '{"goal":"实现一个系统","scope":"先完成核心流程","outputs":{"primary_deliverable":"系统代码","report":"最终 Markdown 报告"},'
                '"acceptance":{"definition":"功能可用","must_have":["页面可访问","流程可演示"]},'
                '"missing_info":[{"key":"target_users","question":"目标用户是谁？"},{"key":"core_features","question":"请列出 3-5 个核心功能。"}]}'
            ),
        }

    def _mock_llm_no_missing(self, mock_generate, deliverable: str = "任务管理网站代码") -> None:
        mock_generate.return_value = {
            "provider_type": "openai_compatible",
            "model": "mock-model",
            "content": (
                '{"goal":"实现一个任务管理网站","scope":"实现任务流程与日志","outputs":{"primary_deliverable":"'
                + deliverable
                + '","report":"最终 Markdown 报告"},'
                '"acceptance":{"definition":"可创建任务并查看实时日志","must_have":["核心流程可演示"]},"missing_info":[]}'
            ),
        }

    @patch("app.agents.requirement_analyzer.llm_service.generate_text")
    def test_task_enters_clarification_when_missing_info(self, mock_generate) -> None:
        self._mock_llm_missing_info(mock_generate)
        task_id = task_orchestrator.create_task(
            title="Need details",
            prompt="做一个系统",
            env_profile_id=self.profile["id"],
        )
        task = TaskRepository().get_task(task_id)
        self.assertEqual(task["status"], "WAITING_USER_INPUT")
        self.assertIsNotNone(ClarificationRepository().get_pending_round(task_id))

    @patch("app.agents.requirement_analyzer.llm_service.generate_text")
    def test_task_decomposes_after_clarification(self, mock_generate) -> None:
        self._mock_llm_missing_info(mock_generate)
        task_id = task_orchestrator.create_task(
            title="Build system",
            prompt="实现一个有 UI 和后端 agent 编排的系统",
            env_profile_id=self.profile["id"],
        )
        self._mock_llm_no_missing(mock_generate, "完整产品")
        self._answer_all_pending_questions(task_id, "补充")
        subtasks = SubTaskRepository().list_by_task(task_id)
        self.assertGreaterEqual(len(subtasks), 2)

    @patch("app.agents.requirement_analyzer.llm_service.generate_text")
    def test_runtime_isolation_context_created_for_subtasks(self, mock_generate) -> None:
        self._mock_llm_missing_info(mock_generate)
        task_id = task_orchestrator.create_task(
            title="Build site",
            prompt="创建一个网站，包含前后端和任务调度",
            env_profile_id=self.profile["id"],
        )
        self._mock_llm_no_missing(mock_generate, "可运行的网站代码")
        self._answer_all_pending_questions(task_id, "补充")
        subtasks = SubTaskRepository().list_by_task(task_id)
        self.assertGreaterEqual(len(subtasks), 2)
        for subtask in subtasks:
            runtime = subtask["input_context"].get("runtime")
            self.assertIsNotNone(runtime)
            self.assertTrue(Path(runtime["workspace_path"]).exists())
            self.assertTrue(Path(runtime["manifest_path"]).exists())
            self.assertGreaterEqual(len(runtime["skill_files"]), 1)
            self.assertTrue(subtask["agent_template"].startswith("tmp_"))

    @patch("app.agents.requirement_analyzer.llm_service.generate_text")
    def test_disable_auto_sub_agents_keeps_static_templates(self, mock_generate) -> None:
        self._mock_llm_missing_info(mock_generate)
        profile_id = self.env_repo.create_profile(
            name="No Auto Agent",
            provider_type="openai_compatible",
            api_base_url="https://example.com/v1",
            api_key="test-key",
            default_model="gpt-mock",
            review_model="gpt-mock-review",
            test_model="gpt-mock-test",
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
        self._mock_llm_no_missing(mock_generate, "后端代码")
        self._answer_all_pending_questions(task_id, "补充")
        subtasks = SubTaskRepository().list_by_task(task_id)
        self.assertGreaterEqual(len(subtasks), 1)
        self.assertFalse(any(item["agent_template"].startswith("tmp_") for item in subtasks))

    @patch("app.agents.requirement_analyzer.llm_service.generate_text")
    def test_auto_title_generated_from_requirement_when_title_missing(self, mock_generate) -> None:
        self._mock_llm_no_missing(mock_generate, "任务管理网站代码")
        task_id = task_orchestrator.create_task(
            title=None,
            prompt="实现一个任务管理网站，支持看板、筛选和实时日志",
            env_profile_id=self.profile["id"],
        )
        task = TaskRepository().get_task(task_id)
        self.assertEqual(task["title"], "任务管理网站代码")
        self.assertEqual(int(task["title_auto_generated"]), 1)

    @patch("app.agents.requirement_analyzer.llm_service.generate_text")
    def test_manual_title_is_not_overwritten(self, mock_generate) -> None:
        self._mock_llm_no_missing(mock_generate, "任务管理网站代码")
        task_id = task_orchestrator.create_task(
            title="固定标题",
            prompt="实现一个任务管理网站，支持看板、筛选和实时日志",
            env_profile_id=self.profile["id"],
        )
        task = TaskRepository().get_task(task_id)
        self.assertEqual(task["title"], "固定标题")
        self.assertEqual(int(task["title_auto_generated"]), 0)

    @patch("app.agents.requirement_analyzer.llm_service.generate_text")
    def test_task_waits_when_ai_returns_invalid_json(self, mock_generate) -> None:
        mock_generate.return_value = {
            "provider_type": "openai_compatible",
            "model": "mock-model",
            "content": "not-json",
        }
        task_id = task_orchestrator.create_task(
            title="Invalid analysis",
            prompt="实现一个系统",
            env_profile_id=self.profile["id"],
        )
        task = TaskRepository().get_task(task_id)
        self.assertEqual(task["status"], "WAITING_USER_INPUT")


if __name__ == "__main__":
    unittest.main()
