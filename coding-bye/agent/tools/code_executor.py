from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

from agent.tools.base import Tool


def build_code_executor(workspace: Path) -> Tool:
    def run(payload: Dict[str, Any]) -> Dict[str, Any]:
        file_path = (workspace / str(payload["path"])).resolve()
        if workspace not in file_path.parents and file_path != workspace:
            raise ValueError("Path escapes workspace")
        proc = subprocess.run(
            ["python", str(file_path)],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=int(payload.get("timeout_seconds", 30)),
        )
        return {"returncode": proc.returncode, "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-8000:]}

    return Tool(
        name="code_executor",
        description="Run a Python file in workspace",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        run=run,
    )

