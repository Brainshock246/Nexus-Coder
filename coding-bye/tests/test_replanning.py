import unittest

from agent.core.reflector import Reflector


class ReplanningTests(unittest.TestCase):
    def test_reflector_triggers_replan_for_repeated_error(self) -> None:
        reflector = Reflector()
        reflection = reflector.reflect(
            {"success": False, "error": "timeout waiting for tool", "error_streak": 3, "repeated_error": True}
        )
        self.assertFalse(reflection.success)
        self.assertTrue(reflection.trigger_replan)


if __name__ == "__main__":
    unittest.main()
