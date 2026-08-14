"""Retry a model call through a rate limit.

A long film makes thousands of calls, and Vertex answers some of them with 429. That is
not an error in the work, it is backpressure, and the right response is to wait and try
again rather than lose an hour of extraction to a transient limit. Exponential backoff,
capped, and it gives up loudly after enough tries rather than silently returning nothing.
"""
from __future__ import annotations

import time


def with_retry(fn, *, tries: int = 6, base: float = 4.0):
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - 429 and transient 5xx are worth retrying
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "503" in msg or "UNAVAILABLE" in msg:
                last = e
                time.sleep(min(base * (2 ** i), 60.0))
                continue
            raise
    raise last if last else RuntimeError("retry exhausted")
