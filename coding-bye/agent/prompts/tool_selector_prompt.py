from __future__ import annotations


def build_tool_selector_prompt(task: str, candidate_tools: list[str]) -> str:
    return (
        "Score each tool for this task and return JSON only with schema "
        '{"scores":[{"tool":"...","score":0.0}],"selected":"...","args":{}}. '
        f"Task: {task}. Candidates: {candidate_tools}"
    )

