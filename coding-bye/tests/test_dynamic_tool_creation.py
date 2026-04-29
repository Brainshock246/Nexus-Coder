import tempfile
import unittest
from pathlib import Path

from agent.tools.registry import ToolRegistry


class DynamicToolTests(unittest.TestCase):
    def test_dynamic_tool_creation_and_registration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugins = Path(tmp)
            registry = ToolRegistry()
            registry.create_and_register_dynamic_tool("auto_tool", "generated", plugins)
            self.assertIn("auto_tool", list(registry.names()))


if __name__ == "__main__":
    unittest.main()
