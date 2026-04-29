from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HierarchyRole:
    name: str
    responsibility: str


SUPERVISOR = HierarchyRole("SupervisorAgent", "Manage lifecycle and orchestration of all child agents.")
PLANNER = HierarchyRole("PlannerAgent", "Decompose goals and produce task tree.")
EXECUTOR = HierarchyRole("ExecutorAgent", "Execute tools and code actions safely.")
REVIEWER = HierarchyRole("ReviewerAgent", "Review outcomes and identify regressions.")
RESEARCHER = HierarchyRole("ResearchAgent", "Collect external/internal evidence.")
OPTIMIZER = HierarchyRole("OptimizerAgent", "Improve performance and prompt/tool choices.")

