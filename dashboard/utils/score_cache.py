"""Shared, bounded full-score cache and compatible snapshot lookup.

The cache is intentionally process-local: it removes repeat work across pages
and sessions served by one Streamlit worker without pretending that a cron
process can warm a different web process. Durable first-paint support comes
from the compatible database snapshot lookup below.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable, MutableMapping

from utils.model_version import MODEL_VERSION, signal_registry_version
from utils.performance import notify_progress, record_timing


FULL_SCORE_TTL_SECONDS = 1800
FULL_SCORE_MAX_ENTRIES = 256


@dataclass(frozen=True)
class FullScoreCacheKey:
    ticker: str
    signal_mode: str
    signal_ids: tuple[str, ...]
    include_optional: bool
    model_version: str
    signal_registry_version: str
    freshness_bucket: int


@dataclass(frozen=True)
class FullScoreOutcome:
    result: dict
    key: FullScoreCacheKey
    cache_status: str
    duration_seconds: float


def canonical_signal_ids(signal_ids: Iterable[str] | None) -> tuple[str, tuple[str, ...]]:
    """Keep None (automatic selection) distinct from an explicit empty set."""
    if signal_ids is None:
        return "auto", ()
    normalized = tuple(sorted({str(s).strip() for s in signal_ids if str(s).strip()}))
    return "explicit", normalized


def make_full_score_cache_key(
    ticker: str,
    signal_ids: Iterable[str] | None,
    include_optional: bool,
    *,
    now: float | None = None,
    model_version: str = MODEL_VERSION,
    registry_version: str | None = None,
) -> FullScoreCacheKey:
    mode, signals = canonical_signal_ids(signal_ids)
    epoch = time.time() if now is None else float(now)
    return FullScoreCacheKey(
        ticker=str(ticker).upper().strip(),
        signal_mode=mode,
        signal_ids=signals,
        include_optional=bool(include_optional),
        model_version=str(model_version),
        signal_registry_version=registry_version or signal_registry_version(),
        freshness_bucket=int(epoch // FULL_SCORE_TTL_SECONDS),
    )


class FullScoreCache:
    """Small thread-safe LRU with per-key de-duplication and targeted clears."""

    def __init__(self, max_entries: int = FULL_SCORE_MAX_ENTRIES):
        self.max_entries = int(max_entries)
        self._entries: OrderedDict[FullScoreCacheKey, dict] = OrderedDict()
        self._lock = threading.RLock()
        self._key_locks: dict[FullScoreCacheKey, threading.Lock] = {}

    def _get(self, key: FullScoreCacheKey) -> dict | None:
        with self._lock:
            result = self._entries.get(key)
            if result is not None:
                self._entries.move_to_end(key)
            return result

    def get_or_compute(
        self,
        key: FullScoreCacheKey,
        compute: Callable[[], dict],
    ) -> tuple[dict, str]:
        hit = self._get(key)
        if hit is not None:
            return hit, "hit"
        with self._lock:
            key_lock = self._key_locks.setdefault(key, threading.Lock())
        with key_lock:
            hit = self._get(key)
            if hit is not None:
                return hit, "hit"
            try:
                result = compute()  # exceptions and partial failures are never cached
                if not result.get("is_complete", True):
                    return result, "miss_degraded"
                with self._lock:
                    self._entries[key] = result
                    self._entries.move_to_end(key)
                    while len(self._entries) > self.max_entries:
                        self._entries.popitem(last=False)
                return result, "miss"
            finally:
                with self._lock:
                    self._key_locks.pop(key, None)

    def clear_key(self, key: FullScoreCacheKey) -> bool:
        with self._lock:
            return self._entries.pop(key, None) is not None

    def put(self, key: FullScoreCacheKey, result: dict) -> bool:
        """Prime one complete result; provisional results are rejected."""
        if not result.get("is_complete", True):
            return False
        with self._lock:
            self._entries[key] = result
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)
        return True

    def clear_ticker(self, ticker: str) -> int:
        normalized = str(ticker).upper().strip()
        with self._lock:
            keys = [key for key in self._entries if key.ticker == normalized]
            for key in keys:
                self._entries.pop(key, None)
            return len(keys)

    def clear_result(
        self,
        ticker: str,
        signal_ids: Iterable[str] | None,
        include_optional: bool,
    ) -> int:
        probe = make_full_score_cache_key(ticker, signal_ids, include_optional)
        with self._lock:
            keys = [
                key for key in self._entries
                if (
                    key.ticker == probe.ticker
                    and key.signal_mode == probe.signal_mode
                    and key.signal_ids == probe.signal_ids
                    and key.include_optional == probe.include_optional
                )
            ]
            for key in keys:
                self._entries.pop(key, None)
            return len(keys)

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


_SHARED_FULL_SCORE_CACHE = FullScoreCache()


def get_full_ticker_score(
    ticker: str,
    signal_ids: Iterable[str] | None = None,
    *,
    include_optional: bool = True,
    progress_callback: Callable[[str, str], None] | None = None,
) -> FullScoreOutcome:
    """Return the canonical full result from the shared worker cache."""
    from utils.ticker_score import compute_full_ticker_score

    key = make_full_score_cache_key(ticker, signal_ids, include_optional)
    started = time.perf_counter()

    def _compute() -> dict:
        notify_progress(progress_callback, "macro_signals", "Loading macro signals…")
        explicit = None if key.signal_mode == "auto" else list(key.signal_ids)
        return compute_full_ticker_score(
            key.ticker,
            signal_ids=explicit,
            include_optional=key.include_optional,
            progress_callback=progress_callback,
        )

    cached = _SHARED_FULL_SCORE_CACHE._get(key)
    if cached is not None:
        notify_progress(progress_callback, "cached_score", "Loading cached score…")
        result, status = cached, "hit"
    else:
        result, status = _SHARED_FULL_SCORE_CACHE.get_or_compute(key, _compute)
    duration = time.perf_counter() - started
    record_timing(
        "full_score_cache",
        ticker=key.ticker,
        duration_seconds=duration,
        success=status != "miss_degraded",
        cache_status=status,
        metadata={"include_optional": key.include_optional, "signal_mode": key.signal_mode},
    )
    return FullScoreOutcome(result=result, key=key, cache_status=status, duration_seconds=duration)


def clear_full_score_result(
    ticker: str,
    signal_ids: Iterable[str] | None = None,
    *,
    include_optional: bool = True,
) -> int:
    return _SHARED_FULL_SCORE_CACHE.clear_result(ticker, signal_ids, include_optional)


def clear_full_scores_for_ticker(ticker: str) -> int:
    return _SHARED_FULL_SCORE_CACHE.clear_ticker(ticker)


def prime_full_score_result(
    ticker: str,
    result: dict,
    signal_ids: Iterable[str] | None = None,
    *,
    include_optional: bool = True,
) -> bool:
    key = make_full_score_cache_key(ticker, signal_ids, include_optional)
    return _SHARED_FULL_SCORE_CACHE.put(key, result)


def session_result_key(key: FullScoreCacheKey) -> str:
    payload = json.dumps(key.__dict__, sort_keys=True, separators=(",", ":"))
    return "full_score::" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def get_session_result(
    state: MutableMapping,
    key: FullScoreCacheKey,
) -> dict | None:
    return state.get("_full_score_session_results", {}).get(session_result_key(key))


def set_session_result(
    state: MutableMapping,
    key: FullScoreCacheKey,
    result: dict,
) -> None:
    results = state.setdefault("_full_score_session_results", {})
    results[session_result_key(key)] = result
    # A user session only needs a small working set; bound it independently.
    while len(results) > 12:
        results.pop(next(iter(results)))


def clear_session_result(state: MutableMapping, key: FullScoreCacheKey) -> bool:
    return state.get("_full_score_session_results", {}).pop(session_result_key(key), None) is not None


def get_latest_compatible_full_snapshot(
    ticker: str,
    signal_ids: Iterable[str] | None,
) -> dict | None:
    """Return only a complete, current-model snapshot with the same signals."""
    from sqlalchemy import and_, select
    from utils import db
    from utils.db import score_components, score_snapshots

    mode, expected_signals = canonical_signal_ids(signal_ids)
    if mode != "explicit":
        return None  # Compatibility cannot be proven without an explicit set.
    try:
        joined = score_snapshots.join(
            score_components,
            and_(
                score_snapshots.c.ticker == score_components.c.ticker,
                score_snapshots.c.snapshot_date == score_components.c.snapshot_date,
            ),
        )
        with db.engine.begin() as conn:
            row = conn.execute(
                select(
                    score_snapshots.c.ticker,
                    score_snapshots.c.snapshot_date,
                    score_snapshots.c.score,
                    score_snapshots.c.case,
                    score_snapshots.c.conviction,
                    score_snapshots.c.created_at,
                    score_snapshots.c.score_kind,
                    score_components.c.model_version,
                    score_components.c.signal_registry_version,
                    score_components.c.components_json,
                )
                .select_from(joined)
                .where(score_snapshots.c.ticker == str(ticker).upper().strip())
                .where(score_snapshots.c.score_kind == "full")
                .where(score_components.c.model_version == MODEL_VERSION)
                .where(score_components.c.signal_registry_version == signal_registry_version())
                .order_by(score_snapshots.c.snapshot_date.desc())
                .limit(1)
            ).mappings().first()
        if not row:
            return None
        components = json.loads(row["components_json"])
        stored_signals = tuple(sorted(str(s.get("id", "")) for s in components.get("signals", []) if s.get("id")))
        if stored_signals != expected_signals:
            return None
        calculated_at = components.get("calculated_at") or row["created_at"]
        calculated_dt = datetime.fromisoformat(str(calculated_at).replace("Z", "+00:00"))
        if calculated_dt.tzinfo is None:
            calculated_dt = calculated_dt.replace(tzinfo=timezone.utc)
        return {
            "ticker": row["ticker"],
            "snapshot_date": row["snapshot_date"],
            "score": float(row["score"]),
            "case": row["case"],
            "conviction": row["conviction"],
            "score_kind": "full",
            "model_version": row["model_version"],
            "signal_registry_version": row["signal_registry_version"],
            "calculated_at": calculated_dt.astimezone(timezone.utc).isoformat(),
            "age_seconds": max(0, int((datetime.now(timezone.utc) - calculated_dt.astimezone(timezone.utc)).total_seconds())),
            "components": components,
        }
    except Exception:
        return None
