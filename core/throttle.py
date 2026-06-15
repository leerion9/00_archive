"""HTTP throttle for Naver crawling (from moa HistoryCacheStore pattern)."""

from __future__ import annotations

import logging
import random
import time

_log = logging.getLogger("archive")


class RequestThrottler:
    def __init__(
        self,
        *,
        delay_sec: float = 0.08,
        jitter_sec: float = 0.03,
        batch_size: int = 50,
        batch_pause_sec: float = 3.0,
    ) -> None:
        self.delay_sec = max(0.0, float(delay_sec))
        self.jitter_sec = max(0.0, float(jitter_sec))
        self.batch_size = max(1, int(batch_size))
        self.batch_pause_sec = max(0.0, float(batch_pause_sec))
        self._request_count = 0

    def after_request(self) -> None:
        self._request_count += 1
        jitter = random.uniform(0.0, self.jitter_sec) if self.jitter_sec > 0 else 0.0
        time.sleep(self.delay_sec + jitter)
        if self._request_count % self.batch_size != 0:
            return
        extra = random.uniform(0.5, 1.5)
        pause = self.batch_pause_sec + extra
        _log.info("[throttle] batch pause %.1fs after %d requests", pause, self._request_count)
        time.sleep(pause)

    @property
    def request_count(self) -> int:
        return self._request_count
