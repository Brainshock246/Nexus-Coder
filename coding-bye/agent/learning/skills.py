from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class SkillLibrary:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def save_skill(self, name: str, strategy: str, tags: List[str]) -> None:
        skills = self.list_skills()
        skills.append({"name": name, "strategy": strategy, "tags": tags})
        self.path.write_text(json.dumps(skills, indent=2), encoding="utf-8")

    def list_skills(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def search(self, query: str) -> List[Dict[str, Any]]:
        lowered = query.lower()
        return [
            s for s in self.list_skills() if lowered in s.get("name", "").lower() or lowered in s.get("strategy", "").lower()
        ]

