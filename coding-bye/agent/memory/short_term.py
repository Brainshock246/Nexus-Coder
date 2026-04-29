from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class ShortTermMemory:
    def __init__(self, path: Path, max_items: int = 100) -> None:
        self.path = path
        self.max_items = max_items
        self._items: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            self._items = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self._items = []

    def add(self, item: Dict[str, Any]) -> None:
        self._items.append(item)
        self._items = self._items[-self.max_items :]
        self.path.write_text(json.dumps(self._items, indent=2), encoding="utf-8")

    def recent(self, n: int = 10) -> List[Dict[str, Any]]:
        return self._items[-n:]

    def reset(self) -> None:
        self._items = []
        self.path.write_text("[]", encoding="utf-8")

