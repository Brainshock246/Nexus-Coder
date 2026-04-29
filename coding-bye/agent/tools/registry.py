from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Dict, Iterable, List

from agent.tools.base import Tool
from agent.tools.dynamic_tool_creator import DynamicToolCreator


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}
        self.dynamic_creator: DynamicToolCreator | None = None

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def names(self) -> Iterable[str]:
        return self._tools.keys()

    def load_plugins(self, plugins_dir: Path) -> List[str]:
        self.dynamic_creator = DynamicToolCreator(plugins_dir)
        loaded: List[str] = []
        for path in plugins_dir.glob("*.py"):
            if path.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(path.stem, path)
            if not spec or not spec.loader:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            register_fn = getattr(module, "register", None)
            if callable(register_fn):
                register_fn(self)
                loaded.append(path.name)
        return loaded

    def create_and_register_dynamic_tool(self, tool_name: str, behavior_hint: str, plugins_dir: Path) -> str:
        if not self.dynamic_creator:
            self.dynamic_creator = DynamicToolCreator(plugins_dir)
        path = self.dynamic_creator.create_tool(tool_name, behavior_hint)
        self.load_plugins(plugins_dir)
        return str(path)

