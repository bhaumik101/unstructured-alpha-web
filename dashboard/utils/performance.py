"""Lightweight, privacy-safe performance timing for core product paths."""

from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Callable, Iterator


_LOGGER = logging.getLogger("unstructured_alpha.performance")


def record_timing(
    stage: str,
    *,
    ticker: str = "",
    duration_seconds: float,
    success: bool,
    cache_status: str = "not_applicable",
    metadata: dict | None = None,
) -> dict:
    """Emit one structured timing record without user or session identifiers."""
    event = {
        "event": "performance_timing",
        "stage": str(stage),
        "ticker": str(ticker).upper().strip(),
        "cache_status": str(cache_status),
        "duration_seconds": round(float(duration_seconds), 6),
        "success": bool(success),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if metadata:
        event["metadata"] = {
            str(k): v for k, v in metadata.items()
            if isinstance(v, (str, int, float, bool)) or v is None
        }
    _LOGGER.info("PERF %s", json.dumps(event, sort_keys=True, default=str))
    return event


@contextmanager
def timed_stage(
    stage: str,
    *,
    ticker: str,
    events: list[dict] | None = None,
    cache_status: str = "not_applicable",
    metadata: dict | None = None,
    outcome: dict | None = None,
) -> Iterator[None]:
    """Measure a block, log failures, and preserve the original exception."""
    started = time.perf_counter()
    ok = False
    try:
        yield
        ok = True
    finally:
        measured_success = ok and bool((outcome or {}).get("success", True))
        event = record_timing(
            stage,
            ticker=ticker,
            duration_seconds=time.perf_counter() - started,
            success=measured_success,
            cache_status=cache_status,
            metadata=metadata,
        )
        if events is not None:
            events.append(event)


def notify_progress(
    callback: Callable[[str, str], None] | None,
    stage: str,
    message: str,
) -> None:
    """Progress callbacks are best-effort and must never break scoring."""
    if callback is None:
        return
    try:
        callback(stage, message)
    except Exception:
        pass
