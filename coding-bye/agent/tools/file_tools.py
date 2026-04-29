from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from agent.tools.base import Tool


def _safe(workspace: Path, raw_path: str) -> Path:
    full = (workspace / raw_path).resolve()
    if workspace not in full.parents and full != workspace:
        raise ValueError("Path escapes workspace")
    return full


def build_file_tools(workspace: Path) -> list[Tool]:
    def read_file(payload: Dict[str, Any]) -> Dict[str, Any]:
        path = _safe(workspace, str(payload["path"]))
        text = path.read_text(encoding="utf-8")
        return {"path": str(path.relative_to(workspace)), "content": text}

    def write_file(payload: Dict[str, Any]) -> Dict[str, Any]:
        path = _safe(workspace, str(payload["path"]))
        content = str(payload.get("content", ""))
        append = bool(payload.get("append", False))
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with path.open(mode, encoding="utf-8") as handle:
            handle.write(content)
        return {"path": str(path.relative_to(workspace)), "bytes": len(content.encode("utf-8"))}

    def list_dir(payload: Dict[str, Any]) -> Dict[str, Any]:
        path = _safe(workspace, str(payload.get("path", ".")))
        entries = [p.name for p in sorted(path.iterdir())]
        return {"path": str(path.relative_to(workspace)), "entries": entries}

    def delete_file(payload: Dict[str, Any]) -> Dict[str, Any]:
        path = _safe(workspace, str(payload["path"]))
        existed = path.exists()
        if path.is_file():
            path.unlink()
        return {"path": str(path.relative_to(workspace)), "deleted": existed}

    return [
        Tool(
            name="file_reader",
            description="Read file content from workspace",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            run=read_file,
        ),
        Tool(
            name="file_writer",
            description="Write or append file content in workspace",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "append": {"type": "boolean"},
                },
                "required": ["path", "content"],
            },
            run=write_file,
        ),
        Tool(
            name="directory_lister",
            description="List files and folders in a workspace directory",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
            run=list_dir,
        ),
        Tool(
            name="file_delete",
            description="Delete a file in workspace",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            run=delete_file,
        ),
    ]

