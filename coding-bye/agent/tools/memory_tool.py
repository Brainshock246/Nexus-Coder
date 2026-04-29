from __future__ import annotations

from typing import Any, Dict

from agent.memory.long_term import LongTermMemory
from agent.tools.base import Tool


def build_memory_tool(memory: LongTermMemory) -> Tool:
    def run(payload: Dict[str, Any]) -> Dict[str, Any]:
        action = str(payload.get("action", "search"))
        if action == "write":
            idx = memory.write(
                category=str(payload.get("category", "general")),
                content=str(payload.get("content", "")),
                metadata=payload.get("metadata", {}),
            )
            return {"stored_id": idx}
        if action == "read":
            return {"items": memory.read(limit=int(payload.get("limit", 10)))}
        if action == "summary":
            return {"summary": memory.summarize(limit=int(payload.get("limit", 30)))}
        return {"items": memory.search(query=str(payload.get("query", "")), limit=int(payload.get("limit", 10)))}

    return Tool(
        name="memory_tool",
        description="Write/read/search long-term memory store",
        input_schema={"type": "object", "properties": {"action": {"type": "string"}}},
        run=run,
    )

