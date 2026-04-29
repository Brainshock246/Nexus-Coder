from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class PromptEvolutionEngine:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def record(self, prompt_name: str, success: bool, feedback: str) -> None:
        records = self.records()
        records.append({"prompt": prompt_name, "success": success, "feedback": feedback})
        self.path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def records(self) -> List[Dict[str, object]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def evolve(self, prompt_text: str, prompt_name: str) -> str:
        failed = [r for r in self.records() if r.get("prompt") == prompt_name and not r.get("success")]
        if len(failed) < 2:
            return prompt_text
        return prompt_text + "\n\nConstraint: provide concise, validated JSON and include fallback args."

