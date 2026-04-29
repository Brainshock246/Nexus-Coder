import unittest

from agent.multi_agent.hierarchy.manager import HierarchicalManager


class HierarchyTests(unittest.TestCase):
    def test_supervisor_flow_runs_chain(self) -> None:
        manager = HierarchicalManager()
        runs = manager.supervisor_flow("improve performance")
        self.assertGreaterEqual(len(runs), 5)
        self.assertEqual(runs[0].state, "completed")


if __name__ == "__main__":
    unittest.main()
