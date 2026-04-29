import unittest

from agent.multi_agent.manager import MultiAgentManager


class MultiAgentTests(unittest.TestCase):
    def test_manager_dispatches_worker(self) -> None:
        manager = MultiAgentManager()
        result = manager.dispatch("planner", {"goal": "build feature"})
        self.assertEqual(result.role, "PlannerAgent")
        self.assertIn("goal", result.output["received_task"])


if __name__ == "__main__":
    unittest.main()
