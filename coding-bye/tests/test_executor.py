import unittest

from agent.core.executor import Executor
from agent.core.planner import PlanTask
from agent.tools.base import Tool
from agent.tools.registry import ToolRegistry


class ExecutorTests(unittest.TestCase):
    def test_executor_runs_selected_tool(self) -> None:
        registry = ToolRegistry()
        registry.register(Tool("memory_tool", "test tool", {}, lambda payload: {"ok": True, "payload": payload}))
        registry.register(Tool("file_reader", "", {}, lambda payload: {"ok": True}))
        registry.register(Tool("file_writer", "", {}, lambda payload: {"ok": True}))
        registry.register(Tool("directory_lister", "", {}, lambda payload: {"ok": True}))
        registry.register(Tool("web_search", "", {}, lambda payload: {"ok": True}))
        registry.register(Tool("web_scraper", "", {}, lambda payload: {"ok": True}))
        registry.register(Tool("json_tool", "", {}, lambda payload: {"ok": True}))
        registry.register(Tool("python_tool", "", {}, lambda payload: {"ok": True}))
        registry.register(Tool("shell_command", "", {}, lambda payload: {"ok": True}))
        executor = Executor(registry=registry, timeout_seconds=2)
        result = executor.execute(PlanTask(task_id=1, description="unknown task"))
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()

