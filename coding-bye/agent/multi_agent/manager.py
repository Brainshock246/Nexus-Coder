from __future__ import annotations

from typing import Any, Dict, List

from agent.distributed.executor import DistributedExecutor
from agent.multi_agent.agent_role import EXECUTOR_AGENT, PLANNER_AGENT, REVIEWER_AGENT
from agent.multi_agent.worker import Worker, WorkerResult


class MultiAgentManager:
    def __init__(self) -> None:
        self.distributed = DistributedExecutor(workers=3)
        self.workers = {
            "planner": Worker(PLANNER_AGENT),
            "executor": Worker(EXECUTOR_AGENT),
            "reviewer": Worker(REVIEWER_AGENT),
        }

    def dispatch(self, role_key: str, task: Dict[str, Any]) -> WorkerResult:
        worker = self.workers[role_key]
        return worker.run(task)

    def available_roles(self) -> List[str]:
        return sorted(self.workers.keys())

    def dispatch_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        payloads = [{"task": t} for t in tasks]
        return self.distributed.run_parallel(lambda p: {"received": p["task"]}, payloads)

