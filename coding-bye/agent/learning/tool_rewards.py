from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List


class ToolRewardStore:
    def __init__(self, db_path: Path) -> None:
        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT NOT NULL,
                reward REAL NOT NULL
            )
            """
        )
        self.conn.commit()

    def record(self, tool_name: str, reward: float) -> None:
        self.conn.execute("INSERT INTO tool_rewards (tool_name, reward) VALUES (?, ?)", (tool_name, reward))
        self.conn.commit()

    def ranking(self) -> List[Dict[str, float]]:
        rows = self.conn.execute(
            "SELECT tool_name, AVG(reward) as avg_reward FROM tool_rewards GROUP BY tool_name ORDER BY avg_reward DESC"
        ).fetchall()
        return [{"tool_name": row[0], "avg_reward": float(row[1])} for row in rows]

