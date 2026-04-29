from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable, Dict

from agent.tools.base import Tool


def build_shell_tool(
    workspace: Path,
    approval_callback: Callable[[str], bool],
    timeout_seconds: int = 45,
) -> Tool:
    blocked_snippets = ["rm -rf /", "del /f /s /q", "format ", "shutdown", "reboot", ":(){:|:&};:"]

    def run_command(payload: Dict[str, Any]) -> Dict[str, Any]:
        command = str(payload["command"])
        lowered = command.lower()
        if any(token in lowered for token in blocked_snippets):
            return {"blocked": True, "reason": "dangerous command pattern detected"}
        if not approval_callback(command):
            return {"blocked": True, "reason": "command approval denied by user"}
        proc = subprocess.run(
            command,
            cwd=str(workspace),
            shell=True,
            capture_output=True,
            text=True,
            timeout=int(payload.get("timeout_seconds", timeout_seconds)),
        )
        return {
            "blocked": False,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-8000:],
            "stderr": proc.stderr[-8000:],
        }

    return Tool(
        name="shell_command",
        description="Run shell command with safety checks and approval",
        input_schema={"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
        run=run_command,
    )

