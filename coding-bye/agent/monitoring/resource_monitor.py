from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Dict


@dataclass
class ResourceSnapshot:
    cpu_seconds: float
    rss_mb: float
    wall_time: float


class ResourceMonitor:
    def __init__(self, cpu_limit_s: float = 120.0, memory_limit_mb: float = 1024.0) -> None:
        self.cpu_limit_s = cpu_limit_s
        self.memory_limit_mb = memory_limit_mb
        self.started = time.time()

    def snapshot(self) -> ResourceSnapshot:
        cpu = time.process_time()
        rss_mb = 0.0
        try:
            import psutil  # type: ignore

            rss_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
        except Exception:
            pass
        return ResourceSnapshot(cpu_seconds=cpu, rss_mb=rss_mb, wall_time=time.time() - self.started)

    def limits_exceeded(self) -> Dict[str, bool]:
        snap = self.snapshot()
        return {
            "cpu": snap.cpu_seconds > self.cpu_limit_s,
            "memory": snap.rss_mb > self.memory_limit_mb if snap.rss_mb else False,
            "wall": snap.wall_time > self.cpu_limit_s * 2,
        }

