from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


class MemoryCompressor:
    def compress(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for item in traces:
            tool = str(item.get("action", {}).get("tool", "unknown"))
            grouped[tool].append(item)
        summary = []
        for tool, events in grouped.items():
            success_count = sum(1 for event in events if event.get("reflection", {}).get("success"))
            summary.append(
                {
                    "tool": tool,
                    "events": len(events),
                    "success_ratio": success_count / max(len(events), 1),
                    "common_improvement": events[-1].get("reflection", {}).get("improvement", ""),
                }
            )
        return {"summary": sorted(summary, key=lambda x: x["events"], reverse=True)}

