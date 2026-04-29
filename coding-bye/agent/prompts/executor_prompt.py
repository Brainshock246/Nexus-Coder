from __future__ import annotations


def build_executor_prompt(task: str, tools: list[str]) -> str:
    return (
        "Select the best tool and arguments. Return JSON only with schema "
        '{"tool":"name","args":{},"confidence":0.0,"reason":"..."} '
        f"Task: {task}. Available tools: {tools}"
    )

