from __future__ import annotations

import unittest

from agent.tools.plugin_security import validate_plugin_source


class PluginSecurityTests(unittest.TestCase):
    def test_validate_plugin_source_accepts_safe_code(self) -> None:
        source = """
from agent.tools.base import Tool

def register(registry):
    def run(payload):
        return {"ok": True, "payload": payload}
    registry.register(Tool(name="x", description="", input_schema={"type": "object"}, run=run))
"""
        issues = validate_plugin_source(source)
        self.assertEqual(issues, [])

    def test_validate_plugin_source_rejects_forbidden_calls(self) -> None:
        source = """
def register(registry):
    exec("print(1)")
"""
        issues = validate_plugin_source(source)
        self.assertTrue(any("Forbidden call: exec" in issue.message for issue in issues))

    def test_validate_plugin_source_rejects_forbidden_import(self) -> None:
        source = """
import subprocess
"""
        issues = validate_plugin_source(source)
        self.assertTrue(any("Forbidden import: subprocess" in issue.message for issue in issues))

    def test_validate_plugin_source_rejects_open_write_mode(self) -> None:
        source = """
def register(registry):
    f = open("x.txt", "w")
    f.close()
"""
        issues = validate_plugin_source(source)
        self.assertTrue(any("open in write mode" in issue.message for issue in issues))


if __name__ == "__main__":
    unittest.main()
