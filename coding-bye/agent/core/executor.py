from __future__ import annotations

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from typing import Any, Dict, List

from agent.learning.tool_rewards import ToolRewardStore
from agent.llm.provider import LLMProvider
from agent.llm.router import ModelRouter
from agent.prompts import build_executor_prompt, build_tool_selector_prompt
from agent.rag.retriever import RetrievalEngine
from agent.core.planner import PlanTask
from agent.tools.registry import ToolRegistry


@dataclass
class ExecutionResult:
    success: bool
    tool_name: str
    payload: Dict[str, Any]
    output: str
    error: str = ""
    classification: str = "recoverable"
    latency_ms: int = 0


class Executor:
    def __init__(
        self,
        registry: ToolRegistry,
        timeout_seconds: int = 45,
        max_retries: int = 2,
        llm_provider: LLMProvider | None = None,
        cache_ttl_seconds: int = 600,
        reward_store: ToolRewardStore | None = None,
        retriever: RetrievalEngine | None = None,
    ) -> None:
        self.registry = registry
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.llm_provider = llm_provider
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_time: Dict[str, float] = {}
        self._last_errors: List[str] = []
        self.reward_store = reward_store
        self.retriever = retriever
        self.model_router = ModelRouter()

    def _pick_tool(self, task_description: str) -> tuple[str, Dict[str, Any]]:
        names = list(self.registry.names())
        if self.retriever:
            _ = self.retriever.retrieve(task_description, limit=2)
        if self.llm_provider and names:
            result = self._llm_select_tool(task_description, names)
            if result:
                return result
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

    def _llm_select_tool(self, task_description: str, names: List[str]) -> tuple[str, Dict[str, Any]] | None:
        try:
            route = self.model_router.route(task_description)
            if self.llm_provider and hasattr(self.llm_provider, "model"):
                provider_name = self.llm_provider.__class__.__name__.lower()
                if route.provider in provider_name:
                    setattr(self.llm_provider, "model", route.model)
            score_prompt = build_tool_selector_prompt(task_description, names)
            score_resp = self.llm_provider.generate(score_prompt, temperature=0.0, max_tokens=300)
            parsed_score = json.loads(score_resp.text or "{}")
            selected = str(parsed_score.get("selected", "")).strip()
            args = parsed_score.get("args", {})
            if selected in names and isinstance(args, dict):
                return selected, args
        except Exception:
            pass
        try:
            prompt = build_executor_prompt(task_description, names)
            resp = self.llm_provider.generate(prompt, temperature=0.1, max_tokens=300)
            parsed = json.loads(resp.text or "{}")
            tool_name = str(parsed.get("tool", "")).strip()
            args = parsed.get("args", {})
            if tool_name in names and isinstance(args, dict):
                return tool_name, args
        except Exception:
            return None
        return None

    def _classify_error(self, message: str) -> str:
        lower = message.lower()
        if "unknown tool" in lower or "permission denied" in lower or "blocked" in lower:
            return "non-recoverable"
        if "timeout" in lower or "tempor" in lower or "network" in lower:
            return "recoverable"
        return "recoverable"

    async def execute_async(self, task: PlanTask) -> ExecutionResult:
        return await asyncio.to_thread(self.execute, task)

    def execute(self, task: PlanTask) -> ExecutionResult:
        start = time.perf_counter()
        tool_name, payload = self._pick_tool(task.description)
        cache_key = f"{tool_name}:{json.dumps(payload, sort_keys=True)}"
        if cache_key in self._cache and (time.time() - self._cache_time.get(cache_key, 0) < self.cache_ttl_seconds):
            cached = self._cache[cache_key]
            return ExecutionResult(
                True,
                tool_name,
                payload,
                json.dumps(cached),
                latency_ms=int((time.perf_counter() - start) * 1000),
            )

        tool = self.registry.get(tool_name)
        last_error = ""
        for _ in range(self.max_retries + 1):
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(tool.run, payload)
                try:
                    result = future.result(timeout=self.timeout_seconds)
                    self._cache[cache_key] = result
                    self._cache_time[cache_key] = time.time()
                    if self.reward_store:
                        self.reward_store.record(tool_name, 1.0)
                    return ExecutionResult(
                        success=True,
                        tool_name=tool_name,
                        payload=payload,
                        output=json.dumps(result, indent=2),
                        latency_ms=int((time.perf_counter() - start) * 1000),
                    )
                except FutureTimeoutError:
                    last_error = f"Tool timeout after {self.timeout_seconds}s"
                except Exception as exc:  # noqa: BLE001
                    last_error = str(exc)
        if self.reward_store:
            self.reward_store.record(tool_name, -1.0)
        self._last_errors.append(last_error)
        repeated = self._last_errors.count(last_error) >= 2 if last_error else False
        classification = self._classify_error(last_error)

        # Fallback strategy for recoverable failures.
        if classification == "recoverable" and tool_name != "memory_tool":
            try:
                fallback = self.registry.get("memory_tool")
                fallback_result = fallback.run({"action": "search", "query": task.description})
                return ExecutionResult(
                    success=True,
                    tool_name="memory_tool",
                    payload={"action": "search", "query": task.description},
                    output=json.dumps(
                        {
                            "fallback": True,
                            "original_error": last_error,
                            "result": fallback_result,
                            "repeated_error": repeated,
                        },
                        indent=2,
                    ),
                    latency_ms=int((time.perf_counter() - start) * 1000),
                )
            except Exception:
                pass

        return ExecutionResult(
            success=False,
            tool_name=tool_name,
            payload=payload,
            output="",
            error=last_error,
            classification=classification,
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

