from __future__ import annotations

import importlib.util
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List

from agent.tools.base import Tool
from agent.tools.dynamic_tool_creator import DynamicToolCreator
from agent.tools.plugin_security import file_sha256, validate_plugin_source


logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(
        self,
        *,
        enable_dynamic_tools: bool = False,
        confirm_plugin_load: Callable[[str], bool] | None = None,
    ) -> None:
        self._tools: Dict[str, Tool] = {}
        self.dynamic_creator: DynamicToolCreator | None = None
        self.enable_dynamic_tools = enable_dynamic_tools
        self.confirm_plugin_load = confirm_plugin_load

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        # Fix for incorrect tool naming
        if name == "python_tool":
            name = "code_executor"

        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def names(self) -> Iterable[str]:
        return self._tools.keys()

    def load_plugins(self, plugins_dir: Path) -> List[str]:
        if not self.enable_dynamic_tools:
            logger.info("Dynamic plugin loading disabled for this session.")
            return []
        self.dynamic_creator = DynamicToolCreator(plugins_dir)
        loaded: List[str] = []
        for path in plugins_dir.glob("*.py"):
            if path.name.startswith("_"):
                continue
            if not self._can_load_plugin(path):
                continue
            spec = importlib.util.spec_from_file_location(path.stem, path)
            if not spec or not spec.loader:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            register_fn = getattr(module, "register", None)
            if callable(register_fn):
                register_fn(self)
                self._log_plugin_load(path)
                loaded.append(path.name)
        return loaded

    def create_and_register_dynamic_tool(self, tool_name: str, behavior_hint: str, plugins_dir: Path) -> str:
        if not self.enable_dynamic_tools:
            raise RuntimeError("Dynamic tool creation is disabled for this session.")
        if not self.dynamic_creator:
            self.dynamic_creator = DynamicToolCreator(plugins_dir)
        path = self.dynamic_creator.create_tool(tool_name, behavior_hint)
        self.load_plugins(plugins_dir)
        return str(path)

    def _can_load_plugin(self, path: Path) -> bool:
        source = path.read_text(encoding="utf-8")
        issues = validate_plugin_source(source)
        if issues:
            issue_summary = ", ".join(f"line {issue.line}: {issue.message}" for issue in issues)
            logger.error("Plugin AST safety check failed for %s: %s", path.name, issue_summary)
            return False
        logger.info("Plugin AST safety check passed for %s", path.name)
        if not self.confirm_plugin_load:
            logger.warning("Plugin %s blocked: no confirmation callback configured.", path.name)
            return False
        if not self.confirm_plugin_load(path.name):
            logger.warning("Plugin %s blocked: user confirmation denied.", path.name)
            return False
        return True

    def _log_plugin_load(self, path: Path) -> None:
        logger.info(
            "Dynamic plugin loaded name=%s sha256=%s timestamp=%s",
            path.name,
            file_sha256(path),
            datetime.now(timezone.utc).isoformat(),
        )
