from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from agent.multi_agent.agent_role import AgentRole


@dataclass
class WorkerResult:
    role: str
    output: Dict[str, Any]


class Worker:
    def __init__(self, role: AgentRole) -> None:
        self.role = role

    def run(self, task: Dict[str, Any]) -> WorkerResult:
        return WorkerResult(role=self.role.name, output={"received_task": task, "objective": self.role.objective})

