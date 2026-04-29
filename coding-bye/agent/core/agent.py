from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

from agent.config import AgentConfig
from agent.core.executor import Executor
from agent.core.planner import Plan, Planner
from agent.core.reflector import Reflector
from agent.memory.long_term import LongTermMemory
from agent.memory.short_term import ShortTermMemory


@dataclass
class AgentState:
    goal: str = ""
    plan: Plan | None = None
    status: str = "idle"
    step_count: int = 0
    error_count: int = 0
    traces: List[Dict[str, Any]] = field(default_factory=list)


class AgentCore:
    def __init__(
        self,
        config: AgentConfig,
        planner: Planner,
        executor: Executor,
        reflector: Reflector,
        short_memory: ShortTermMemory,
        long_memory: LongTermMemory,
    ) -> None:
        self.config = config
        self.planner = planner
        self.executor = executor
        self.reflector = reflector
        self.short_memory = short_memory
        self.long_memory = long_memory
        self.state = AgentState()
        self.logger = self._build_logger()

    def _build_logger(self) -> logging.Logger:
        logger = logging.getLogger("agent_trace")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.FileHandler(self.config.logs_dir / "agent.log", encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
            logger.addHandler(handler)
        return logger

    def set_goal(self, goal: str) -> None:
        self.state.goal = goal
        self.state.plan = self.planner.create_plan(goal)
        self.state.status = "planned"
        self.state.step_count = 0
        self.state.error_count = 0
        self.state.traces.clear()

    def reset(self) -> None:
        self.state = AgentState()
        self.short_memory.reset()

    def run_once(self) -> Dict[str, Any]:
        if not self.state.plan:
            raise RuntimeError("No active goal. Use /goal first.")
        task = self.state.plan.next_task()
        if not task:
            self.state.status = "complete"
            return {"done": True, "message": "Goal complete"}

        self.state.status = "running"
        self.state.step_count += 1
        task.attempts += 1

        thought = f"Need to complete task {task.task_id}: {task.description}"
        exec_result = self.executor.execute(task)
        reflection = self.reflector.reflect(
            {"success": exec_result.success, "output": exec_result.output, "error": exec_result.error}
        )

        if exec_result.success:
            task.status = "done"
            task.result = exec_result.output
            self.long_memory.write("task_result", exec_result.output, {"task_id": task.task_id})
        else:
            self.state.error_count += 1
            if task.attempts >= 2:
                task.status = "failed"
                self.state.plan = self.planner.replan(self.state.plan, exec_result.error or task.description)

        trace = {
            "thought": thought,
            "action": {"tool": exec_result.tool_name, "payload": exec_result.payload},
            "result": exec_result.output if exec_result.success else exec_result.error,
            "reflection": {"success": reflection.success, "notes": reflection.notes, "improvement": reflection.improvement},
        }
        self.state.traces.append(trace)
        self.short_memory.add(trace)
        self.logger.info(json.dumps(trace))

        if self.state.error_count >= self.config.error_limit:
            self.state.status = "stopped"
        elif not self.state.plan.next_task():
            self.state.status = "complete"
        return {"done": self.state.status in {"complete", "stopped"}, "trace": trace}

    def run_until_done(self) -> Dict[str, Any]:
        while self.state.status not in {"complete", "stopped"}:
            if self.state.step_count >= self.config.max_steps:
                self.state.status = "stopped"
                break
            self.run_once()
        return {
            "status": self.state.status,
            "steps": self.state.step_count,
            "errors": self.state.error_count,
            "remaining_tasks": len(self.state.plan.pending()) if self.state.plan else 0,
        }

