from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class LongTermMemory:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def write(self, category: str, content: str, metadata: Dict[str, Any] | None = None) -> int:
        payload = json.dumps(metadata or {})
        cur = self.conn.execute(
            "INSERT INTO memories (category, content, metadata) VALUES (?, ?, ?)",
            (category, content, payload),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def read(self, limit: int = 20) -> List[Dict[str, Any]]:
        cur = self.conn.execute(
            "SELECT id, category, content, metadata, created_at FROM memories ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "category": row[1],
                "content": row[2],
                "metadata": json.loads(row[3]),
                "created_at": row[4],
            }
            for row in rows
        ]

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        cur = self.conn.execute(
            """
            SELECT id, category, content, metadata, created_at
            FROM memories
            WHERE content LIKE ? OR category LIKE ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", limit),
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "category": row[1],
                "content": row[2],
                "metadata": json.loads(row[3]),
                "created_at": row[4],
            }
            for row in rows
        ]

    def summarize(self, limit: int = 30) -> str:
        entries = self.read(limit=limit)
        if not entries:
            return "No long-term memories yet."
        categories: Dict[str, int] = {}
        for item in entries:
            categories[item["category"]] = categories.get(item["category"], 0) + 1
        chunks = [f"{name}: {count}" for name, count in sorted(categories.items())]
        return "Memory summary -> " + ", ".join(chunks)

    def close(self) -> None:
        self.conn.close()

