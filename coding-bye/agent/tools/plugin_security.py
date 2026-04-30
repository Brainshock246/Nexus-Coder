from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


FORBIDDEN_IMPORTS = {"os", "sys", "subprocess"}
FORBIDDEN_CALLS = {"exec", "eval"}


@dataclass(frozen=True)
class ValidationIssue:
    message: str
    line: int


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _imported_modules(node: ast.AST) -> Iterable[str]:
    if isinstance(node, ast.Import):
        for alias in node.names:
            yield alias.name.split(".")[0]
    if isinstance(node, ast.ImportFrom) and node.module:
        yield node.module.split(".")[0]


def _is_write_open_call(node: ast.Call) -> bool:
    if not isinstance(node.func, ast.Name) or node.func.id != "open":
        return False
    mode = ""
    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
        arg = node.args[1].value
        if isinstance(arg, str):
            mode = arg
    for keyword in node.keywords:
        if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
            arg = keyword.value.value
            if isinstance(arg, str):
                mode = arg
    return any(flag in mode for flag in ("w", "a", "+", "x"))


def validate_plugin_source(source: str) -> list[ValidationIssue]:
    tree = ast.parse(source)
    issues: list[ValidationIssue] = []
    for node in ast.walk(tree):
        for module_name in _imported_modules(node):
            if module_name in FORBIDDEN_IMPORTS:
                issues.append(ValidationIssue(f"Forbidden import: {module_name}", getattr(node, "lineno", 0)))
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            issues.append(ValidationIssue(f"Forbidden call: {node.func.id}", getattr(node, "lineno", 0)))
        if _is_write_open_call(node):
            issues.append(ValidationIssue("Forbidden call: open in write mode", getattr(node, "lineno", 0)))
    return issues
