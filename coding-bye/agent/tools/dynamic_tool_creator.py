from __future__ import annotations

from pathlib import Path


class DynamicToolCreator:
    def __init__(self, plugins_dir: Path) -> None:
        self.plugins_dir = plugins_dir
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

    def create_tool(self, tool_name: str, behavior_hint: str) -> Path:
        safe_name = tool_name.lower().replace(" ", "_")
        target = self.plugins_dir / f"{safe_name}.py"
        code = f'''from agent.tools.base import Tool


def register(registry):
    def run(payload):
        return {{"tool": "{safe_name}", "hint": "{behavior_hint}", "payload": payload}}
    registry.register(
        Tool(
            name="{safe_name}",
            description="Dynamically generated tool: {behavior_hint}",
            input_schema={{"type": "object"}},
            run=run,
        )
    )
'''
        target.write_text(code, encoding="utf-8")
        return target

