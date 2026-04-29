from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class KnowledgeGraph:
    def __init__(self, db_path: Path) -> None:
        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type TEXT NOT NULL,
                key TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                src_key TEXT NOT NULL,
                dst_key TEXT NOT NULL,
                edge_type TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def upsert_node(self, node_type: str, key: str, content: str) -> None:
        self.conn.execute(
            """
            INSERT INTO nodes (node_type, key, content) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET node_type=excluded.node_type, content=excluded.content
            """,
            (node_type, key, content),
        )
        self.conn.commit()

    def add_edge(self, src_key: str, dst_key: str, edge_type: str) -> None:
        self.conn.execute(
            "INSERT INTO edges (src_key, dst_key, edge_type) VALUES (?, ?, ?)",
            (src_key, dst_key, edge_type),
        )
        self.conn.commit()

    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        rows = self.conn.execute(
            "SELECT node_type, key, content FROM nodes WHERE content LIKE ? OR key LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()
        return {"matches": [{"node_type": r[0], "key": r[1], "content": r[2]} for r in rows]}

    def discover_relationships(self, key: str) -> Dict[str, List[Dict[str, str]]]:
        outgoing = self.conn.execute(
            "SELECT dst_key, edge_type FROM edges WHERE src_key = ?",
            (key,),
        ).fetchall()
        incoming = self.conn.execute(
            "SELECT src_key, edge_type FROM edges WHERE dst_key = ?",
            (key,),
        ).fetchall()
        return {
            "outgoing": [{"to": row[0], "edge_type": row[1]} for row in outgoing],
            "incoming": [{"from": row[0], "edge_type": row[1]} for row in incoming],
        }

    def close(self) -> None:
        self.conn.close()

