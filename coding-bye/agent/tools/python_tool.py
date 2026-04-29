from __future__ import annotations

import contextlib
import io
from typing import Any, Dict

from agent.tools.base import Tool


def build_python_tool() -> Tool:
    def run(payload: Dict[str, Any]) -> Dict[str, Any]:
        code = str(payload.get("code", ""))
        globals_scope: Dict[str, Any] = {"__builtins__": __builtins__}
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exec(code, globals_scope, {})  # noqa: S102
        return {"stdout": stdout.getvalue()}

    return Tool(
        name="python_tool",
        description="Execute Python code snippets in isolated scope",
        input_schema={"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]},
        run=run,
    )

