from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class WorkspaceIndexer:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def build_index(self) -> Dict[str, Any]:
        files = []
        ext_groups: Dict[str, int] = {}
        for path in self.workspace_root.rglob("*"):
            if not path.is_file():
                continue
            rel = str(path.relative_to(self.workspace_root))
            ext = path.suffix.lower() or "<none>"
            ext_groups[ext] = ext_groups.get(ext, 0) + 1
            files.append(
                {
                    "path": rel,
                    "type": ext,
                    "size": path.stat().st_size,
                    "last_modified": int(path.stat().st_mtime),
                    "relationships": {"parent": str(path.parent.relative_to(self.workspace_root))},
                }
            )
        return {"root": str(self.workspace_root), "file_count": len(files), "file_types": ext_groups, "files": files}

    def write_index(self, output_path: Path) -> Dict[str, Any]:
        index = self.build_index()
        output_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
        return index

