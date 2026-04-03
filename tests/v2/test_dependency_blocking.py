from __future__ import annotations

import unittest

from app.v2.modules.tasks.dependency_resolver import block_dependents


class DependencyBlockingTestCase(unittest.TestCase):
    def test_block_dependents_marks_downstream_nodes(self) -> None:
        subtasks = [
            {"id": "a", "status": "NEEDS_HUMAN_REVIEW"},
            {"id": "b", "status": "PENDING"},
            {"id": "c", "status": "PENDING"},
        ]
        dependencies = [
            {"from_sub_task_id": "a", "to_sub_task_id": "b"},
            {"from_sub_task_id": "b", "to_sub_task_id": "c"},
        ]
        blocked = block_dependents(subtasks, dependencies, failed_subtask_id="a")
        self.assertEqual(blocked, ["b", "c"])


if __name__ == "__main__":
    unittest.main()
