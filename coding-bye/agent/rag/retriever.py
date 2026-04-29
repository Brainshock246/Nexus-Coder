from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from agent.rag.vector_store import VectorStore


class RetrievalEngine:
    def __init__(self) -> None:
        self.store = VectorStore()

    def index_workspace(self, workspace: Path) -> None:
        for path in workspace.rglob("*"):
            if path.is_file() and path.stat().st_size < 200_000:
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                self.store.upsert(f"file:{path}", text[:4000])

    def index_memory(self, traces: list[Dict[str, Any]]) -> None:
        for i, trace in enumerate(traces):
            self.store.upsert(f"trace:{i}", str(trace))

    def retrieve(self, query: str, limit: int = 5) -> Dict[str, Any]:
        items = self.store.search(query, limit=limit)
        return {"results": [{"key": k, "score": s, "text": t[:200]} for k, s, t in items]}

