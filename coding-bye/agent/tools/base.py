from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Protocol


class ToolRunner(Protocol):
    def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...


@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    run: Callable[[Dict[str, Any]], Dict[str, Any]]

