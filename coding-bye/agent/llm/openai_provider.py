from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict

from agent.llm.provider import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    def __init__(self, *, base_url: str, model: str, api_key: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> LLMResponse:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAIProvider")
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = json.loads(response.read().decode("utf-8"))
        text = str(raw.get("choices", [{}])[0].get("message", {}).get("content", "")).strip()
        return LLMResponse(text=text, raw=raw)

