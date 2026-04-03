from __future__ import annotations

import unittest

from app.v2.core.models import EnvProfile
from app.v2.modules.capabilities.generator import (
    build_agent_candidate,
    build_skill_candidate,
)


class CapabilityGenerationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = EnvProfile(
            name="demo",
            provider_type="demo",
            api_base_url="",
            api_key="",
            default_model="demo-heuristic",
            review_model="",
            test_model="",
            capability_generation_model="demo-cap",
            report_model="",
            temperature=0.2,
            default_timeout_sec=300,
            max_retries=2,
            max_concurrency=2,
            enable_docker_sandbox=True,
            enable_auto_sub_agents=True,
        )
        self.task = {"id": "task-1", "title": "构建控制台", "prompt": "实现任务工作台和运行监控"}
        self.subtask = {
            "id": "sub-1",
            "name": "实现前端工作台",
            "description": "完成任务工作台、运行监控和环境配置视图。",
            "category": "ui",
            "acceptance": {"must_have": ["任务工作台"]},
        }

    def test_build_agent_candidate_tracks_generation_metadata(self) -> None:
        payload = build_agent_candidate(self.task, self.subtask, self.profile)
        self.assertIn("generation_model", payload)
        self.assertEqual(payload["generation_model"], "demo-cap")
        self.assertIn("frontend", payload["name"])

    def test_build_skill_candidate_has_whitelisted_command(self) -> None:
        payload = build_skill_candidate(self.task, self.subtask, self.profile)
        self.assertGreaterEqual(len(payload["allowed_commands"]), 1)
        self.assertEqual(payload["allowed_file_scope"], ["/workspace"])


if __name__ == "__main__":
    unittest.main()
