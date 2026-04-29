from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Dict

from agent.tools.base import Tool


def build_code_executor(workspace: Path) -> Tool:
    def _try_self_heal(file_path: Path, stderr: str) -> bool:
        original = file_path.read_text(encoding="utf-8")
        updated = original
        if "NameError: name 'json' is not defined" in stderr and "import json" not in updated:
            updated = "import json\n" + updated
        if "NameError: name 'sys' is not defined" in stderr and "import sys" not in updated:
            updated = "import sys\n" + updated
        syntax_match = re.search(r"SyntaxError: expected an indented block", stderr)
        if syntax_match and "pass" not in updated:
            updated += "\n\nif __name__ == '__main__':\n    pass\n"
        if updated != original:
            file_path.write_text(updated, encoding="utf-8")
            return True
        return False

    def _run_tests() -> Dict[str, Any]:
        proc = subprocess.run(
            ["python", "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {"returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}

    def run(payload: Dict[str, Any]) -> Dict[str, Any]:
        file_path = (workspace / str(payload["path"])).resolve()
        if workspace not in file_path.parents and file_path != workspace:
            raise ValueError("Path escapes workspace")
        retry_limit = int(payload.get("retry_limit", 3))
        last = {"returncode": 1, "stdout": "", "stderr": ""}
        healed = 0
        for _ in range(retry_limit + 1):
            proc = subprocess.run(
                ["python", str(file_path)],
                cwd=str(workspace),
                capture_output=True,
                text=True,
                timeout=int(payload.get("timeout_seconds", 30)),
            )
            last = {"returncode": proc.returncode, "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-8000:]}
            if proc.returncode == 0:
                tests = _run_tests()
                return {**last, "self_healed": healed > 0, "tests": tests}
            if _try_self_heal(file_path, proc.stderr):
                healed += 1
                continue
            break
        tests = _run_tests()
        return {**last, "self_healed": healed > 0, "heal_attempts": healed, "tests": tests}

    return Tool(
        name="code_executor",
        description="Run a Python file in workspace",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        run=run,
    )

