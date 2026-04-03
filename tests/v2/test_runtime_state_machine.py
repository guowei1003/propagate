from __future__ import annotations

import unittest

from app.v2.modules.runtime.state_machine import derive_run_status_and_phase


class RuntimeStateMachineTestCase(unittest.TestCase):
    def test_all_completed_maps_to_done(self) -> None:
        status, phase = derive_run_status_and_phase(
            [{"status": "COMPLETED"}, {"status": "COMPLETED"}],
            all_success=True,
        )
        self.assertEqual(status, "COMPLETED")
        self.assertEqual(phase, "DONE")

    def test_terminal_mixed_maps_to_partial_success_done(self) -> None:
        status, phase = derive_run_status_and_phase(
            [{"status": "COMPLETED"}, {"status": "BLOCKED_BY_DEPENDENCY"}],
            all_success=False,
        )
        self.assertEqual(status, "PARTIAL_SUCCESS")
        self.assertEqual(phase, "DONE")

    def test_non_terminal_remains_running(self) -> None:
        status, phase = derive_run_status_and_phase(
            [{"status": "COMPLETED"}, {"status": "PENDING"}],
            all_success=False,
        )
        self.assertEqual(status, "RUNNING")
        self.assertEqual(phase, "SUBTASK_RUNNING")


if __name__ == "__main__":
    unittest.main()
