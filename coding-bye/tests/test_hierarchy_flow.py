import unittest

from agent.multi_agent.hierarchy import HierarchicalManager


class HierarchyFlowTests(unittest.TestCase):
    def test_supervisor_routes_and_runs_flow(self) -> None:
        manager = HierarchicalManager()
        result = manager.execute_flow({"description": "research dependency graph strategy"})
        self.assertEqual(result["route"], "ResearchAgent")
        self.assertIn("optimize", result)


if __name__ == "__main__":
    unittest.main()
