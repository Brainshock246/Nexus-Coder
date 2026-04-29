from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Iterable


@dataclass
class LLMResponse:
    text: str
    raw: Dict[str, Any]


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> LLMResponse:
        raise NotImplementedError

    def generate_stream(self, prompt: str, *, temperature: float, max_tokens: int) -> Iterable[str]:
        response = self.generate(prompt, temperature=temperature, max_tokens=max_tokens)
        yield response.text

