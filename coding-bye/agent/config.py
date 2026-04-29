from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentConfig:
    base_url: str
    model: str
    api_key: str
    workspace_dir: Path
    logs_dir: Path
    memory_db_path: Path
    short_memory_path: Path
    plugins_dir: Path
    max_steps: int = 20
    error_limit: int = 5
    timeout_seconds: int = 45
    autonomous_mode: bool = False
    require_approval: bool = True


def ensure_runtime_dirs(config: AgentConfig) -> None:
    config.workspace_dir.mkdir(parents=True, exist_ok=True)
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    config.plugins_dir.mkdir(parents=True, exist_ok=True)
    config.memory_db_path.parent.mkdir(parents=True, exist_ok=True)
    config.short_memory_path.parent.mkdir(parents=True, exist_ok=True)

