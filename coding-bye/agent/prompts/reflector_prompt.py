from __future__ import annotations


def build_reflector_prompt(result: str, errors: int) -> str:
    return (
        "Analyze execution quality. Return JSON only with schema "
        '{"status":"ok|retry|replan","reason":"...","improvement":"..."} '
        f"Result: {result}. Error streak: {errors}"
    )

