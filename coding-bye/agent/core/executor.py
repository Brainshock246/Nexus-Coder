from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from typing import Any, Dict

from agent.core.planner import PlanTask
from agent.tools.registry import ToolRegistry


@dataclass
class ExecutionResult:
    success: bool
    tool_name: str
    payload: Dict[str, Any]
    output: str
    error: str = ""


class Executor:
    def __init__(self, registry: ToolRegistry, timeout_seconds: int = 45, max_retries: int = 2) -> None:
        self.registry = registry
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _pick_tool(self, task_description: str) -> tuple[str, Dict[str, Any]]:
        text = task_description.lower()
        if "read" in text and "file" in text:
            return "file_reader", {"path": "README.md"}
        if "write" in text or "create file" in text:
            return "file_writer", {"path": "agent/workspace/notes.txt", "content": task_description}
        if "list" in text or "directory" in text:
            return "directory_lister", {"path": "."}
        if "search web" in text or "web search" in text:
            return "web_search", {"query": task_description}
        if "http://" in text or "https://" in text or "scrape" in text:
            return "web_scraper", {"url": task_description.split()[-1]}
        if "json" in text:
            return "json_tool", {"operation": "validate", "data": "{}"}
        if "python" in text:
            return "python_tool", {"code": "print('ok')"}
        if "shell" in text or "command" in text:
            return "shell_command", {"command": task_description}
        return "memory_tool", {"action": "search", "query": task_description}

    def execute(self, task: PlanTask) -> ExecutionResult:
        tool_name, payload = self._pick_tool(task.description)
        cache_key = f"{tool_name}:{json.dumps(payload, sort_keys=True)}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            return ExecutionResult(True, tool_name, payload, json.dumps(cached))

        tool = self.registry.get(tool_name)
        last_error = ""
        for _ in range(self.max_retries + 1):
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(tool.run, payload)
                try:
                    result = future.result(timeout=self.timeout_seconds)
                    self._cache[cache_key] = result
                    return ExecutionResult(
                        success=True,
                        tool_name=tool_name,
                        payload=payload,
                        output=json.dumps(result, indent=2),
                    )
                except FutureTimeoutError:
                    last_error = f"Tool timeout after {self.timeout_seconds}s"
                except Exception as exc:  # noqa: BLE001
                    last_error = str(exc)
        return ExecutionResult(
            success=False,
            tool_name=tool_name,
            payload=payload,
            output="",
            error=last_error,
        )

