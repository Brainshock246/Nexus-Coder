import unittest

from agent.core.planner import Planner


class PlannerTests(unittest.TestCase):
    def test_create_plan_decomposes_goal(self) -> None:
        planner = Planner()
        plan = planner.create_plan("build parser and add tests")
        self.assertGreaterEqual(len(plan.tasks), 2)
        self.assertEqual(plan.tasks[0].status, "pending")


if __name__ == "__main__":
    unittest.main()

