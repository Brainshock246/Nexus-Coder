from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


@dataclass
class VectorItem:
    key: str
    text: str
    vector: Dict[str, float]


class VectorStore:
    def __init__(self) -> None:
        self.items: Dict[str, VectorItem] = {}

    def _embed(self, text: str) -> Dict[str, float]:
        vec: Dict[str, float] = {}
        for token in _tokenize(text):
            vec[token] = vec.get(token, 0.0) + 1.0
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        for k in list(vec.keys()):
            vec[k] /= norm
        return vec

    def upsert(self, key: str, text: str) -> None:
        self.items[key] = VectorItem(key=key, text=text, vector=self._embed(text))

    def search(self, query: str, limit: int = 5) -> List[Tuple[str, float, str]]:
        qv = self._embed(query)
        scored: List[Tuple[str, float, str]] = []
        for item in self.items.values():
            score = 0.0
            for token, val in qv.items():
                score += val * item.vector.get(token, 0.0)
            scored.append((item.key, score, item.text))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

