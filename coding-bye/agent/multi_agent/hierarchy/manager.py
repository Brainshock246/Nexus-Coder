from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from agent.multi_agent.hierarchy.roles import EXECUTOR, OPTIMIZER, PLANNER, RESEARCHER, REVIEWER, SUPERVISOR


@dataclass
class AgentRun:
    role: str
    payload: Dict[str, Any]
    state: str


class HierarchicalManager:
    def __init__(self) -> None:
        self.roles = {
            SUPERVISOR.name: SUPERVISOR,
            PLANNER.name: PLANNER,
            EXECUTOR.name: EXECUTOR,
            REVIEWER.name: REVIEWER,
            RESEARCHER.name: RESEARCHER,
            OPTIMIZER.name: OPTIMIZER,
        }
        self.history: List[AgentRun] = []

    def spawn(self, role_name: str, payload: Dict[str, Any]) -> AgentRun:
        run = AgentRun(role=role_name, payload=payload, state="running")
        self.history.append(run)
        return run

    def terminate(self, run: AgentRun, success: bool) -> None:
        run.state = "completed" if success else "failed"

    def supervisor_flow(self, goal: str) -> List[AgentRun]:
        order = [PLANNER.name, RESEARCHER.name, EXECUTOR.name, REVIEWER.name, OPTIMIZER.name]
        runs: List[AgentRun] = []
        for role in order:
            run = self.spawn(role, {"goal": goal})
            self.terminate(run, success=True)
            runs.append(run)
        return runs

    def execute_flow(self, task: Dict[str, Any]) -> Dict[str, Any]:
        description = str(task.get("description", "")).lower()
        route = RESEARCHER.name if "research" in description else PLANNER.name
        run = self.spawn(route, task)
        self.terminate(run, success=True)
        reviewer = self.spawn(REVIEWER.name, {"from": route, "task": task})
        self.terminate(reviewer, success=True)
        optimize = self.spawn(OPTIMIZER.name, {"from": reviewer.role})
        self.terminate(optimize, success=True)
        return {"route": route, "optimize": True, "history_len": len(self.history)}

