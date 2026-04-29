from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict


class TaskGraphMemory:
    def __init__(self, db_path: Path) -> None:
        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type TEXT NOT NULL,
                ref_id TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_ref TEXT NOT NULL,
                to_ref TEXT NOT NULL,
                edge_type TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def upsert_node(self, node_type: str, ref_id: str, content: str) -> None:
        self.conn.execute(
            """
            INSERT INTO nodes (node_type, ref_id, content) VALUES (?, ?, ?)
            ON CONFLICT(ref_id) DO UPDATE SET node_type=excluded.node_type, content=excluded.content
            """,
            (node_type, ref_id, content),
        )
        self.conn.commit()

    def add_edge(self, from_ref: str, to_ref: str, edge_type: str) -> None:
        self.conn.execute(
            "INSERT INTO edges (from_ref, to_ref, edge_type) VALUES (?, ?, ?)",
            (from_ref, to_ref, edge_type),
        )
        self.conn.commit()

    def snapshot(self) -> Dict[str, Any]:
        nodes = self.conn.execute("SELECT node_type, ref_id, content FROM nodes").fetchall()
        edges = self.conn.execute("SELECT from_ref, to_ref, edge_type FROM edges").fetchall()
        return {
            "nodes": [{"node_type": n[0], "ref_id": n[1], "content": n[2]} for n in nodes],
            "edges": [{"from_ref": e[0], "to_ref": e[1], "edge_type": e[2]} for e in edges],
        }

