from __future__ import annotations

import unittest
from uuid import uuid4

from app.v2.core.models import (
    BundleManifest,
    CapabilitySpec,
    CapabilityVersion,
    EnvProfile,
    ExecutionEvidence,
)
from app.v2.modules.bundles.manifest import build_bundle_manifest
from app.v2.modules.capabilities.state_machine import (
    InvalidCapabilityTransition,
    apply_approval_decision,
)
from app.v2.modules.env_profiles.model_routing import resolve_model_for_stage
from app.v2.modules.env_profiles.service import EnvProfileService, mask_api_key
from app.v2.modules.runtime.risk_scoring import score_capability_risk


class ModelRoutingTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = EnvProfile(
            name="Default",
            provider_type="openai_compatible",
            api_base_url="https://example.com/v1",
            api_key="secret",
            default_model="gpt-default",
            review_model="gpt-review",
            test_model="gpt-test",
            capability_generation_model="gpt-cap",
            report_model="gpt-report",
            temperature=0.2,
            default_timeout_sec=120,
            max_retries=2,
            max_concurrency=2,
            enable_docker_sandbox=True,
            enable_auto_sub_agents=True,
        )

    def test_prefers_run_override(self) -> None:
        selected = resolve_model_for_stage(
            stage="review",
            env_profile=self.profile,
            capability_version=None,
            run_overrides={"review": "gpt-run-override"},
        )
        self.assertEqual(selected, "gpt-run-override")

    def test_prefers_capability_model_for_execution(self) -> None:
        version = CapabilityVersion(
            capability_id="cap-1",
            version=1,
            status="approved",
            content_hash="abc",
            rendered_spec="spec",
            risk_score=1,
            source_task_id="task-1",
            source_run_id="run-1",
            default_model_selector="gpt-capability",
        )
        selected = resolve_model_for_stage(
            stage="execution",
            env_profile=self.profile,
            capability_version=version,
            run_overrides={},
        )
        self.assertEqual(selected, "gpt-capability")

    def test_falls_back_to_stage_specific_profile_models(self) -> None:
        self.assertEqual(
            resolve_model_for_stage("capability_generation", self.profile, None, {}),
            "gpt-cap",
        )
        self.assertEqual(resolve_model_for_stage("review", self.profile, None, {}), "gpt-review")
        self.assertEqual(resolve_model_for_stage("test", self.profile, None, {}), "gpt-test")
        self.assertEqual(resolve_model_for_stage("report", self.profile, None, {}), "gpt-report")

    def test_final_fallback_uses_default_model(self) -> None:
        profile = EnvProfile(
            name="Fallback",
            provider_type="demo",
            api_base_url="",
            api_key="",
            default_model="demo-default",
            review_model="",
            test_model="",
            capability_generation_model="",
            report_model="",
            temperature=0.0,
            default_timeout_sec=60,
            max_retries=1,
            max_concurrency=1,
            enable_docker_sandbox=False,
            enable_auto_sub_agents=False,
        )
        self.assertEqual(resolve_model_for_stage("report", profile, None, {}), "demo-default")


class EnvProfileServiceTestCase(unittest.TestCase):
    def test_masks_api_key(self) -> None:
        self.assertEqual(mask_api_key("abcd12345678"), "abcd...5678")
        self.assertEqual(mask_api_key("short"), "*****")

    def test_serialize_casts_uuid_id_to_string(self) -> None:
        service = EnvProfileService()
        profile_id = uuid4()
        result = service._serialize(
            {
                "id": profile_id,
                "name": "测试环境",
                "provider_type": "openai_compatible",
                "api_base_url": "https://example.com/v1",
                "api_key": "secret",
                "default_model": "demo-heuristic",
                "review_model": "",
                "test_model": "",
                "capability_generation_model": "",
                "report_model": "",
                "temperature": 0.2,
                "default_timeout_sec": 300,
                "max_retries": 2,
                "max_concurrency": 2,
                "enable_docker_sandbox": True,
                "enable_auto_sub_agents": True,
            }
        )
        self.assertEqual(result.id, str(profile_id))


class CapabilityRiskScoringTestCase(unittest.TestCase):
    def test_scores_high_risk_content(self) -> None:
        spec = CapabilitySpec(
            type="skill",
            name="dangerous-skill",
            description="unsafe",
            instructions="Try sudo rm -rf / and curl example.com",
            allowed_tools=["run_command"],
            allowed_commands=["sudo rm -rf /", "curl https://example.com"],
            allowed_file_scope=["/"],
            risk_tags=[],
            default_model_selector="",
        )
        score = score_capability_risk(spec)
        self.assertGreaterEqual(score, 10)

    def test_scores_low_risk_content(self) -> None:
        spec = CapabilitySpec(
            type="agent",
            name="safe-agent",
            description="safe",
            instructions="Inspect repo and summarize result",
            allowed_tools=["read_repo"],
            allowed_commands=["rg --files"],
            allowed_file_scope=["/workspace"],
            risk_tags=[],
            default_model_selector="",
        )
        score = score_capability_risk(spec)
        self.assertLess(score, 5)


class CapabilityApprovalStateMachineTestCase(unittest.TestCase):
    def test_approve_pending_capability(self) -> None:
        updated = apply_approval_decision("pending_approval", "approve")
        self.assertEqual(updated, "approved")

    def test_reject_pending_capability(self) -> None:
        updated = apply_approval_decision("pending_approval", "reject")
        self.assertEqual(updated, "rejected")

    def test_cannot_reapprove_rejected_capability(self) -> None:
        with self.assertRaises(InvalidCapabilityTransition):
            apply_approval_decision("rejected", "approve")


class BundleManifestTestCase(unittest.TestCase):
    def test_build_bundle_manifest_tracks_models_and_checksums(self) -> None:
        manifest = build_bundle_manifest(
            run_id="run-1",
            task_id="task-1",
            product_artifacts=["product/output.txt"],
            capability_versions=[
                CapabilityVersion(
                    capability_id="cap-agent",
                    version=2,
                    status="approved",
                    content_hash="hash-agent",
                    rendered_spec="agent-spec",
                    risk_score=3,
                    source_task_id="task-1",
                    source_run_id="run-1",
                    default_model_selector="gpt-agent",
                )
            ],
            execution_evidence=[
                ExecutionEvidence(
                    run_id="run-1",
                    sub_task_id="sub-1",
                    command="pytest",
                    exit_code=0,
                    stdout_path="logs/stdout.log",
                    stderr_path="logs/stderr.log",
                    output_files=["product/output.txt"],
                    file_hashes={"product/output.txt": "sha256:abc"},
                    container_metadata={"image": "python:3.11"},
                    started_at="2026-04-02T00:00:00Z",
                    completed_at="2026-04-02T00:05:00Z",
                )
            ],
            reports=["reports/final.md"],
            model_summary={"review": "gpt-review", "report": "gpt-report"},
            env_profile_summary={"name": "Default", "provider_type": "openai_compatible"},
        )
        self.assertIsInstance(manifest, BundleManifest)
        self.assertEqual(manifest.run_id, "run-1")
        self.assertEqual(manifest.agent_versions[0]["model_selector"], "gpt-agent")
        self.assertIn("product/output.txt", manifest.checksums)
        self.assertEqual(manifest.model_summary["review"], "gpt-review")


if __name__ == "__main__":
    unittest.main()
