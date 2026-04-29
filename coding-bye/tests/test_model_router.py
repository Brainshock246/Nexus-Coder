import unittest

from agent.llm.model_router import ModelRouter


class ModelRouterTests(unittest.TestCase):
    def test_routes_heavy_coding_task(self) -> None:
        router = ModelRouter()
        routed = router.route("debug and refactor this code")
        self.assertEqual(routed.model, "gpt-4.1")


if __name__ == "__main__":
    unittest.main()
