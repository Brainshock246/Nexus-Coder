from __future__ import annotations

import json
from typing import Any, Dict

from agent.tools.base import Tool


def build_json_tool() -> Tool:
    def run(payload: Dict[str, Any]) -> Dict[str, Any]:
        operation = str(payload.get("operation", "validate"))
        data = payload.get("data", "{}")
        if isinstance(data, (dict, list)):
            parsed = data
        else:
            parsed = json.loads(str(data))
        if operation == "pretty":
            return {"json": json.dumps(parsed, indent=2)}
        if operation == "keys" and isinstance(parsed, dict):
            return {"keys": sorted(parsed.keys())}
        return {"valid": True, "type": type(parsed).__name__}

    return Tool(
        name="json_tool",
        description="Validate and transform JSON payloads",
        input_schema={
            "type": "object",
            "properties": {"operation": {"type": "string"}, "data": {}},
        },
        run=run,
    )

