from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Reflection:
    success: bool
    notes: str
    improvement: str
    trigger_replan: bool = False
    severity: str = "low"


class Reflector:
    def reflect(self, action_result: Dict[str, object]) -> Reflection:
        success = bool(action_result.get("success", False))
        error = str(action_result.get("error", "")).strip()
        output = str(action_result.get("output", "")).strip()
        error_streak = int(action_result.get("error_streak", 0) or 0)
        repeated = bool(action_result.get("repeated_error", False))
        if success:
            return Reflection(
                success=True,
                notes="Action succeeded and produced usable output.",
                improvement="Continue to next task or tighten verification checks.",
            )
        details = error or output or "Unknown failure"
        trigger_replan = repeated or error_streak >= 2 or "timeout" in details.lower()
        return Reflection(
            success=False,
            notes=f"Action failed: {details[:240]}",
            improvement="Retry with adjusted tool/arguments, then replan if repeated failure persists.",
            trigger_replan=trigger_replan,
            severity="high" if trigger_replan else "medium",
        )

