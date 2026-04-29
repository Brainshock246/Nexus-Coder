from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentRole:
    name: str
    objective: str


PLANNER_AGENT = AgentRole("PlannerAgent", "Decompose goals and maintain task priorities.")
EXECUTOR_AGENT = AgentRole("ExecutorAgent", "Run actions safely and efficiently.")
REVIEWER_AGENT = AgentRole("ReviewerAgent", "Review results and suggest improvements.")

