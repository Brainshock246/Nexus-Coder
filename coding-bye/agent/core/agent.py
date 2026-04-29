from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from agent.knowledge.graph import KnowledgeGraph
from agent.learning import PromptEvolutionEngine, SkillLibrary
from agent.memory.compression import MemoryCompressor
from agent.config import AgentConfig
from agent.core.executor import Executor
from agent.core.planner import Plan, Planner
from agent.core.reflector import Reflector
from agent.monitoring.resource_monitor import ResourceMonitor
from agent.memory.long_term import LongTermMemory
from agent.memory.short_term import ShortTermMemory
from agent.memory.task_graph import TaskGraphMemory
from agent.multi_agent.hierarchy import HierarchicalManager
from agent.rag import RetrievalEngine
from agent.workspace.indexer import WorkspaceIndexer


@dataclass
class AgentState:
    goal: str = ""
    plan: Plan | None = None
    status: str = "idle"
    step_count: int = 0
    error_count: int = 0
    traces: List[Dict[str, Any]] = field(default_factory=list)
    session_events: List[Dict[str, Any]] = field(default_factory=list)


class AgentCore:
    def __init__(
        self,
        config: AgentConfig,
        planner: Planner,
        executor: Executor,
        reflector: Reflector,
        short_memory: ShortTermMemory,
        long_memory: LongTermMemory,
        task_graph: TaskGraphMemory,
    ) -> None:
        self.config = config
        self.planner = planner
        self.executor = executor
        self.reflector = reflector
        self.short_memory = short_memory
        self.long_memory = long_memory
        self.task_graph = task_graph
        self.state = AgentState()
        self.logger = self._build_logger()
        self.workspace_indexer = WorkspaceIndexer(config.workspace_dir)
        self.knowledge_graph = KnowledgeGraph(config.logs_dir / "knowledge_graph.db")
        self.resource_monitor = ResourceMonitor()
        self.compressor = MemoryCompressor()
        self.retrieval = RetrievalEngine()
        self.skills = SkillLibrary(config.logs_dir / "skills.json")
        self.prompt_evolution = PromptEvolutionEngine(config.logs_dir / "prompt_evolution.json")
        self.hierarchy = HierarchicalManager()

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
        self.state.session_events.clear()
        self.long_memory.add_task_node("goal", "goal:1", goal)
        self.task_graph.upsert_node("goal", "goal:1", goal)
        self.knowledge_graph.upsert_node("concepts", "goal:1", goal)
        if self.config.workspace_index_path:
            self.workspace_indexer.write_index(self.config.workspace_index_path)
        self.retrieval.index_workspace(self.config.workspace_dir)
        self.hierarchy.supervisor_flow(goal)

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
        limits = self.resource_monitor.limits_exceeded()
        if any(limits.values()):
            self.state.status = "stopped"
            return {"done": True, "message": f"Resource limits exceeded: {limits}"}
        self.state.step_count += 1
        task.attempts += 1
        task_ref = f"task:{task.task_id}"
        self.long_memory.add_task_node("task", task_ref, task.description)
        self.long_memory.add_task_edge("goal:1", task_ref, "contains")
        self.task_graph.upsert_node("task", task_ref, task.description)
        self.task_graph.add_edge("goal:1", task_ref, "contains")
        self.knowledge_graph.upsert_node("tasks", task_ref, task.description)
        self.knowledge_graph.add_edge("goal:1", task_ref, "dependency")

        thought = f"Need to complete task {task.task_id}: {task.description}"
        exec_result = self.executor.execute(task)
        reflection = self.reflector.reflect(
            {
                "success": exec_result.success,
                "output": exec_result.output,
                "error": exec_result.error,
                "error_streak": self.state.error_count,
                "repeated_error": exec_result.classification == "recoverable" and "repeated_error" in exec_result.output,
            }
        )

        if exec_result.success:
            task.status = "done"
            task.result = exec_result.output
            self.long_memory.write("task_result", exec_result.output, {"task_id": task.task_id})
            self.skills.save_skill(f"task-{task.task_id}", f"Successful approach for: {task.description}", ["auto"])
        else:
            self.state.error_count += 1
            if task.attempts >= 2 or reflection.trigger_replan:
                task.status = "failed"
                self.state.plan = self.planner.replan(self.state.plan, exec_result.error or task.description)
        self.long_memory.add_task_node(
            "result",
            f"result:{task.task_id}:{task.attempts}",
            exec_result.output if exec_result.success else exec_result.error,
        )
        self.long_memory.add_task_edge(task_ref, f"result:{task.task_id}:{task.attempts}", "produced")
        self.task_graph.upsert_node(
            "result",
            f"result:{task.task_id}:{task.attempts}",
            exec_result.output if exec_result.success else exec_result.error,
        )
        self.task_graph.add_edge(task_ref, f"result:{task.task_id}:{task.attempts}", "produced")
        self.knowledge_graph.upsert_node(
            "results",
            f"result:{task.task_id}:{task.attempts}",
            exec_result.output if exec_result.success else exec_result.error,
        )
        self.knowledge_graph.add_edge(task_ref, f"result:{task.task_id}:{task.attempts}", "execution flow")

        trace = {
            "timestamp": int(time.time()),
            "thought": thought,
            "action": {"tool": exec_result.tool_name, "payload": exec_result.payload},
            "result": exec_result.output if exec_result.success else exec_result.error,
            "latency_ms": exec_result.latency_ms,
            "reflection": {
                "success": reflection.success,
                "notes": reflection.notes,
                "improvement": reflection.improvement,
                "trigger_replan": reflection.trigger_replan,
                "severity": reflection.severity,
            },
        }
        self.state.traces.append(trace)
        self.state.session_events.append(trace)
        self.short_memory.add(trace)
        self.logger.info(json.dumps(trace))
        self.prompt_evolution.record("executor", exec_result.success, trace["reflection"]["notes"])
        if self.config.session_log_path:
            self.config.session_log_path.write_text(json.dumps(self.state.session_events, indent=2), encoding="utf-8")

        if self.state.error_count >= self.config.error_limit:
            self.state.status = "stopped"
        elif not self.state.plan.next_task():
            self.state.status = "complete"
        return {"done": self.state.status in {"complete", "stopped"}, "trace": trace}

    def discover_goals(self) -> List[str]:
        suggestions: List[str] = []
        if self.state.error_count > 0:
            suggestions.append("Reduce recurring execution errors by improving tool arguments.")
        if self.state.step_count > 5 and self.state.status != "complete":
            suggestions.append("Optimize long-running plan with parallel/distributed execution.")
        compressed = self.compressor.compress(self.state.traces)
        for item in compressed.get("summary", []):
            if float(item.get("success_ratio", 1.0)) < 0.6:
                suggestions.append(f"Improve reliability of tool {item['tool']}.")
        return suggestions[:5]

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

