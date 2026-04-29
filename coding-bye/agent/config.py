from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


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
    provider: str = "openai"
    local_model_url: str = "http://localhost:11434"
    session_log_path: Path | None = None
    workspace_index_path: Path | None = None
    task_graph_db_path: Path | None = None
    cache_ttl_seconds: int = 600


def _parse_simple_yaml(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        data[key.strip()] = value.strip().strip("'").strip('"')
    return data


def load_config_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(parsed, dict):
            return parsed
        return {}
    except Exception:
        return _parse_simple_yaml(path)


def config_from_sources(overrides: Dict[str, Any] | None = None) -> AgentConfig:
    overrides = overrides or {}
    root = Path(".").resolve()
    file_cfg = load_config_file(root / "config.yaml")
    merged: Dict[str, Any] = {}
    merged.update(file_cfg)
    merged.update({k: v for k, v in overrides.items() if v is not None})
    return AgentConfig(
        base_url=str(merged.get("base_url", "https://api.openai.com/v1")),
        model=str(merged.get("model", "gpt-4.1-mini")),
        api_key=str(merged.get("api_key", os.getenv("OPENAI_API_KEY", ""))),
        workspace_dir=(root / str(merged.get("workspace", "agent/workspace"))).resolve(),
        logs_dir=(root / str(merged.get("logs", "agent/logs"))).resolve(),
        memory_db_path=(root / str(merged.get("memory_db", "agent/memory/long_term.db"))).resolve(),
        short_memory_path=(root / str(merged.get("short_memory", "agent/memory/short_term.json"))).resolve(),
        plugins_dir=(root / str(merged.get("plugins", "agent/plugins"))).resolve(),
        max_steps=int(merged.get("max_steps", 20)),
        error_limit=int(merged.get("error_limit", 5)),
        timeout_seconds=int(merged.get("timeout_seconds", 45)),
        autonomous_mode=bool(merged.get("autonomous_mode", False)),
        require_approval=bool(merged.get("require_approval", True)),
        provider=str(merged.get("provider", "openai")),
        local_model_url=str(merged.get("local_model_url", "http://localhost:11434")),
        session_log_path=(root / str(merged.get("session_log", "agent/logs/session.json"))).resolve(),
        workspace_index_path=(root / str(merged.get("workspace_index", "agent/workspace/workspace_index.json"))).resolve(),
        task_graph_db_path=(root / str(merged.get("task_graph_db", "agent/memory/task_graph.db"))).resolve(),
        cache_ttl_seconds=int(merged.get("cache_ttl_seconds", 600)),
    )


def ensure_runtime_dirs(config: AgentConfig) -> None:
    config.workspace_dir.mkdir(parents=True, exist_ok=True)
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    config.plugins_dir.mkdir(parents=True, exist_ok=True)
    config.memory_db_path.parent.mkdir(parents=True, exist_ok=True)
    config.short_memory_path.parent.mkdir(parents=True, exist_ok=True)
    if config.session_log_path:
        config.session_log_path.parent.mkdir(parents=True, exist_ok=True)
    if config.workspace_index_path:
        config.workspace_index_path.parent.mkdir(parents=True, exist_ok=True)
    if config.task_graph_db_path:
        config.task_graph_db_path.parent.mkdir(parents=True, exist_ok=True)

