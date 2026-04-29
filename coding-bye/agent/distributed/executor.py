from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List


class DistributedExecutor:
    """Local thread-based distributed foundation compatible with remote workers later."""

    def __init__(self, workers: int = 4) -> None:
        self.workers = workers

    def run_parallel(self, fn: Callable[[Dict[str, Any]], Dict[str, Any]], payloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = [pool.submit(fn, payload) for payload in payloads]
            return [future.result() for future in futures]

