from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelRoute:
    provider: str
    model: str


class ModelRouter:
    def route(self, task: str) -> ModelRoute:
        lowered = task.lower()
        if "plan" in lowered or "summarize" in lowered:
            return ModelRoute(provider="local", model="llama3.1")
        if "code" in lowered or "debug" in lowered or "refactor" in lowered:
            return ModelRoute(provider="openai", model="gpt-4.1")
        return ModelRoute(provider="local", model="llama3.1")

