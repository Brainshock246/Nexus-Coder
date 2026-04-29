from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict

from agent.llm.provider import LLMProvider, LLMResponse


class LocalProvider(LLMProvider):
    """Local provider compatible with Ollama /api/generate."""

    def __init__(self, *, base_url: str | None = None, model: str = "llama3.1") -> None:
        self.base_url = (base_url or os.getenv("LOCAL_LLM_URL", "http://localhost:11434")).rstrip("/")
        self.model = model

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> LLMResponse:
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = json.loads(response.read().decode("utf-8"))
        text = str(raw.get("response", "")).strip()
        return LLMResponse(text=text, raw=raw)

