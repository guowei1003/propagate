from __future__ import annotations

import os
import unittest

from app.v2.modules.runtime.guardrails import GuardrailViolation, preflight_guard
from app.v2.modules.runtime.review_and_test import evaluate_review, evaluate_test
from app.v2.modules.tasks.dependency_resolver import compute_ready_subtasks
from scripts.run_api import resolve_server_config


class GuardrailsTestCase(unittest.TestCase):
    def test_blocks_unapproved_high_risk_command(self) -> None:
        with self.assertRaises(GuardrailViolation):
            preflight_guard(
                command="sudo rm -rf /",
                allowed_commands=["pytest -q"],
                allowed_file_scope=["/workspace"],
                requested_paths=["/workspace/result.txt"],
            )

    def test_blocks_out_of_scope_path(self) -> None:
        with self.assertRaises(GuardrailViolation):
            preflight_guard(
                command="pytest -q",
                allowed_commands=["pytest -q"],
                allowed_file_scope=["/workspace"],
                requested_paths=["/tmp/outside.txt"],
            )

    def test_accepts_whitelisted_command_and_scope(self) -> None:
        verdict = preflight_guard(
            command="pytest -q",
            allowed_commands=["pytest -q"],
            allowed_file_scope=["/workspace"],
            requested_paths=["/workspace/stdout.log"],
        )
        self.assertTrue(verdict.allowed)


class ReviewAndTestTestCase(unittest.TestCase):
    def test_review_fails_on_todo_marker(self) -> None:
        result = evaluate_review(exit_code=0, stdout_text="TODO: fix", stderr_text="", output_files=["result.txt"])
        self.assertFalse(result.passed)

    def test_test_fails_on_non_zero_exit(self) -> None:
        result = evaluate_test(exit_code=1, stdout_text="failed", stderr_text="traceback")
        self.assertFalse(result.passed)

    def test_review_and_test_pass_on_clean_execution(self) -> None:
        review = evaluate_review(
            exit_code=0,
            stdout_text="done",
            stderr_text="",
            output_files=["result.txt"],
            review_policy={"artifact_required": True, "forbid_todo_markers": True, "require_clean_exit": True},
        )
        test = evaluate_test(exit_code=0, stdout_text="pass", stderr_text="", test_command="pytest -q")
        self.assertTrue(review.passed)
        self.assertTrue(test.passed)


class DependencyResolverTestCase(unittest.TestCase):
    def test_computes_ready_subtasks_from_completed_dependencies(self) -> None:
        subtasks = [
            {"id": "a", "status": "COMPLETED"},
            {"id": "b", "status": "PENDING"},
            {"id": "c", "status": "PENDING"},
        ]
        dependencies = [
            {"from_sub_task_id": "a", "to_sub_task_id": "b"},
            {"from_sub_task_id": "b", "to_sub_task_id": "c"},
        ]
        ready = compute_ready_subtasks(subtasks, dependencies)
        self.assertEqual(ready, ["b"])


class RunApiConfigTestCase(unittest.TestCase):
    def test_defaults_to_public_host(self) -> None:
        old_host = os.environ.pop("HOST", None)
        old_port = os.environ.pop("PORT", None)
        try:
            host, port = resolve_server_config()
            self.assertEqual(host, "0.0.0.0")
            self.assertEqual(port, 8000)
        finally:
            if old_host is not None:
                os.environ["HOST"] = old_host
            if old_port is not None:
                os.environ["PORT"] = old_port


if __name__ == "__main__":
    unittest.main()
