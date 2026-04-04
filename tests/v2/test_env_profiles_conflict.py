from __future__ import annotations

import unittest
from unittest.mock import patch

from app.v2.core.errors import ConflictError
from app.v2.modules.env_profiles.repository import EnvProfileRepository
from app.v2.modules.env_profiles.schemas import EnvProfileCreatePayload, EnvProfileUpdatePayload


class _FakeUniqueViolation(Exception):
    sqlstate = "23505"


class EnvProfilesConflictTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = EnvProfileRepository()

    def _build_create_payload(self) -> EnvProfileCreatePayload:
        return EnvProfileCreatePayload(
            name="测试环境",
            provider_type="openai_compatible",
            api_base_url="https://example.com/v1",
            api_key="secret",
            default_model="demo-heuristic",
            review_model="",
            test_model="",
            capability_generation_model="",
            report_model="",
            temperature=0.2,
            default_timeout_sec=300,
            max_retries=2,
            max_concurrency=2,
            enable_docker_sandbox=True,
            enable_auto_sub_agents=True,
        )

    def _build_update_payload(self) -> EnvProfileUpdatePayload:
        return EnvProfileUpdatePayload(
            name="测试环境",
            provider_type="openai_compatible",
            api_base_url="https://example.com/v1",
            api_key="secret",
            default_model="demo-heuristic",
            review_model="",
            test_model="",
            capability_generation_model="",
            report_model="",
            temperature=0.2,
            default_timeout_sec=300,
            max_retries=2,
            max_concurrency=2,
            enable_docker_sandbox=True,
            enable_auto_sub_agents=True,
        )

    @patch("app.v2.modules.env_profiles.repository.execute", side_effect=_FakeUniqueViolation("duplicate key"))
    def test_create_profile_maps_unique_violation_to_conflict_error(self, _: object) -> None:
        with self.assertRaises(ConflictError) as context:
            self.repository.create_profile(self._build_create_payload())

        self.assertEqual(str(context.exception), "环境配置名称已存在，请更换后重试。")
        self.assertEqual(context.exception.code, "ENV_PROFILE_NAME_CONFLICT")
        self.assertEqual(context.exception.status_code, 409)

    @patch("app.v2.modules.env_profiles.repository.execute", side_effect=_FakeUniqueViolation("duplicate key"))
    def test_update_profile_maps_unique_violation_to_conflict_error(self, _: object) -> None:
        with self.assertRaises(ConflictError) as context:
            self.repository.update_profile("profile-1", self._build_update_payload())

        self.assertEqual(str(context.exception), "环境配置名称已存在，请更换后重试。")
        self.assertEqual(context.exception.code, "ENV_PROFILE_NAME_CONFLICT")
        self.assertEqual(context.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
