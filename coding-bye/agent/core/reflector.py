from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Reflection:
    success: bool
    notes: str
    improvement: str


class Reflector:
    def reflect(self, action_result: Dict[str, object]) -> Reflection:
        success = bool(action_result.get("success", False))
        error = str(action_result.get("error", "")).strip()
        output = str(action_result.get("output", "")).strip()
        if success:
            return Reflection(
                success=True,
                notes="Action succeeded and produced usable output.",
                improvement="Continue to next task or tighten verification checks.",
            )
        details = error or output or "Unknown failure"
        return Reflection(
            success=False,
            notes=f"Action failed: {details[:240]}",
            improvement="Retry with adjusted tool/arguments, then replan if repeated failure persists.",
        )

