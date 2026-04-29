import unittest

from agent.core.executor import Executor
from agent.core.planner import PlanTask
from agent.llm.provider import LLMProvider, LLMResponse
from agent.tools.base import Tool
from agent.tools.registry import ToolRegistry


class FakeProvider(LLMProvider):
    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> LLMResponse:
        return LLMResponse(
            text='{"selected":"file_reader","args":{"path":"README.md"},"scores":[{"tool":"file_reader","score":0.9}]}',
            raw={},
        )


class ToolSelectionTests(unittest.TestCase):
    def test_executor_uses_llm_tool_selection(self) -> None:
        registry = ToolRegistry()
        registry.register(Tool("file_reader", "", {}, lambda payload: {"path": payload["path"], "ok": True}))
        registry.register(Tool("memory_tool", "", {}, lambda payload: {"ok": True}))
        executor = Executor(registry=registry, llm_provider=FakeProvider())
        result = executor.execute(PlanTask(task_id=1, description="read file readme"))
        self.assertTrue(result.success)
        self.assertEqual(result.tool_name, "file_reader")


if __name__ == "__main__":
    unittest.main()
