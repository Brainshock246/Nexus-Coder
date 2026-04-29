from __future__ import annotations


def build_planner_prompt(goal: str) -> str:
    return (
        "You are a task planner. Return JSON only with schema "
        '{"tasks":[{"description":"...","priority":1}]}. '
        f"Goal: {goal}"
    )

