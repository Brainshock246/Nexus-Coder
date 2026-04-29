from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class PlanTask:
    task_id: int
    description: str
    status: str = "pending"
    attempts: int = 0
    result: str = ""


@dataclass
class Plan:
    goal: str
    tasks: List[PlanTask] = field(default_factory=list)

    def pending(self) -> List[PlanTask]:
        return [t for t in self.tasks if t.status == "pending"]

    def next_task(self) -> PlanTask | None:
        for task in self.tasks:
            if task.status == "pending":
                return task
        return None


class Planner:
    def __init__(self, task_tree_path: Path | None = None) -> None:
        self.task_tree_path = task_tree_path

    def _expand_recursive(self, chunk: str, depth: int = 0) -> List[str]:
        if depth >= 2:
            return [chunk]
        lowered = chunk.lower()
        if any(token in lowered for token in ["build", "upgrade", "implement", "create"]):
            return [
                f"Analyze requirements for: {chunk}",
                f"Implement core for: {chunk}",
                f"Validate and optimize: {chunk}",
            ]
        return [chunk]

    def create_plan(self, goal: str) -> Plan:
        raw_chunks = [chunk.strip("- ").strip() for chunk in goal.replace(" and ", ",").split(",")]
        chunks = [c for c in raw_chunks if c]
        if len(chunks) == 1:
            chunks = [
                f"Understand the goal: {goal}",
                "Gather required context and constraints",
                "Execute the primary actions using tools",
                "Validate outputs and finalize deliverables",
            ]
        expanded: List[str] = []
        for chunk in chunks:
            expanded.extend(self._expand_recursive(chunk))
        tasks = [PlanTask(task_id=i + 1, description=desc) for i, desc in enumerate(expanded)]
        if self.task_tree_path:
            tree = {
                "goal": goal,
                "subtasks": [{"id": task.task_id, "description": task.description} for task in tasks],
                "dependencies": [
                    {"from": tasks[i - 1].task_id, "to": tasks[i].task_id} for i in range(1, len(tasks))
                ],
            }
            self.task_tree_path.write_text(json.dumps(tree, indent=2), encoding="utf-8")
        return Plan(goal=goal, tasks=tasks)

    def replan(self, plan: Plan, blocker: str) -> Plan:
        next_id = max((t.task_id for t in plan.tasks), default=0) + 1
        plan.tasks.append(
            PlanTask(
                task_id=next_id,
                description=f"Resolve blocker: {blocker}",
                status="pending",
            )
        )
        return plan

