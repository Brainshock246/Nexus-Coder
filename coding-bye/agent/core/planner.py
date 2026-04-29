from __future__ import annotations

from dataclasses import dataclass, field
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
        tasks = [PlanTask(task_id=i + 1, description=desc) for i, desc in enumerate(chunks)]
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

