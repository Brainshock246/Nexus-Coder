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
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type TEXT NOT NULL,
                ref_id TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_ref TEXT NOT NULL,
                to_ref TEXT NOT NULL,
                edge_type TEXT NOT NULL,
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

    def add_task_node(self, node_type: str, ref_id: str, content: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO task_nodes (node_type, ref_id, content) VALUES (?, ?, ?)",
            (node_type, ref_id, content),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_task_edge(self, from_ref: str, to_ref: str, edge_type: str = "depends_on") -> int:
        cur = self.conn.execute(
            "INSERT INTO task_edges (from_ref, to_ref, edge_type) VALUES (?, ?, ?)",
            (from_ref, to_ref, edge_type),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def read_task_graph(self) -> Dict[str, Any]:
        nodes = self.conn.execute("SELECT node_type, ref_id, content FROM task_nodes ORDER BY id").fetchall()
        edges = self.conn.execute("SELECT from_ref, to_ref, edge_type FROM task_edges ORDER BY id").fetchall()
        return {
            "nodes": [{"node_type": n[0], "ref_id": n[1], "content": n[2]} for n in nodes],
            "edges": [{"from_ref": e[0], "to_ref": e[1], "edge_type": e[2]} for e in edges],
        }

    def close(self) -> None:
        self.conn.close()

