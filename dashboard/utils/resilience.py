"""
utils/resilience.py — lightweight provider resilience: circuit breakers + a
shared, connection-pooled HTTP session with bounded, idempotent-only retries.

Design goals (Phase 5):
  • One shared requests.Session (keep-alive pooling) instead of a fresh
    connection per call.
  • Bounded retries with backoff + jitter for transient 5xx/429 — GET only
    (never retry POST). Respects Retry-After.
  • A per-provider circuit breaker so that when a provider is DOWN, we stop
    hammering it: after N consecutive failures the breaker OPENs and calls
    fail FAST (no network wait) for a cooldown, then HALF-OPEN lets one trial
    through. This prevents a single slow/dead provider from stacking multi-
    second waits across a page (e.g. a Ticker Deep Dive making ~6 SEC calls).

Behavior contract:
  • Healthy path is unchanged — resilient_get/post return the same Response the
    caller already handles; callers keep their own try/except + fallback.
  • On failure (timeout / connection error / open circuit) resilient_get RAISES,
    exactly like a failed requests.get would, so existing `except` blocks catch
    it and return their existing cached/empty fallback.
  • We do NOT call raise_for_status — callers inspect status codes as before, so
    HTTP-level handling is byte-for-byte preserved.
"""

from __future__ import annotations

import logging
import threading
import time

import requests
from requests.adapters import HTTPAdapter

from utils.provider_health import record_provider_event

try:  # urllib3 ships with requests; guard just in case
    from urllib3.util.retry import Retry
    _HAS_RETRY = True
except Exception:  # pragma: no cover
    Retry = None  # type: ignore
    _HAS_RETRY = False

logger = logging.getLogger(__name__)


# ── Circuit breaker ───────────────────────────────────────────────────────────
class CircuitBreaker:
    """
    Per-provider breaker. Thread-safe (scans run under ThreadPoolExecutor).

    CLOSED   → normal; failures increment a counter.
    OPEN     → after `fail_max` consecutive failures; allow() returns False for
               `reset_timeout` seconds (fast-fail, no network).
    HALF-OPEN→ after the cooldown, allow() returns True for ONE trial; a success
               closes the breaker, another failure re-opens it.
    """

    def __init__(self, name: str, fail_max: int = 4, reset_timeout: float = 60.0):
        self.name = name
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self._fails = 0
        self._opened_at = 0.0
        self._lock = threading.Lock()

    def allow(self) -> bool:
        with self._lock:
            if self._fails < self.fail_max:
                return True
            # Breaker is open — permit a single trial once the cooldown elapses.
            return (time.monotonic() - self._opened_at) >= self.reset_timeout

    def record_success(self) -> None:
        with self._lock:
            if self._fails:
                logger.info("[circuit] %s recovered → CLOSED", self.name)
            self._fails = 0
            self._opened_at = 0.0

    def record_failure(self) -> None:
        with self._lock:
            self._fails += 1
            if self._fails >= self.fail_max and self._opened_at == 0.0:
                self._opened_at = time.monotonic()
                logger.warning("[circuit] %s OPEN after %d consecutive failures",
                               self.name, self._fails)
            elif self._opened_at and (time.monotonic() - self._opened_at) >= self.reset_timeout:
                # A half-open trial just failed — restart the cooldown clock.
                self._opened_at = time.monotonic()

    def state(self) -> str:
        with self._lock:
            if self._fails < self.fail_max:
                return "closed"
            return "half_open" if (time.monotonic() - self._opened_at) >= self.reset_timeout else "open"


_breakers: dict[str, CircuitBreaker] = {}
_breakers_lock = threading.Lock()


def get_breaker(name: str, **kw) -> CircuitBreaker:
    with _breakers_lock:
        b = _breakers.get(name)
        if b is None:
            b = _breakers[name] = CircuitBreaker(name, **kw)
        return b


def circuit_states() -> dict[str, str]:
    """Return a safe snapshot for the Data Trust Center."""
    with _breakers_lock:
        return {name: breaker.state() for name, breaker in _breakers.items()}


# ── Shared HTTP session ───────────────────────────────────────────────────────
_session: requests.Session | None = None
_session_lock = threading.Lock()


def get_session() -> requests.Session:
    global _session
    if _session is None:
        with _session_lock:
            if _session is None:
                s = requests.Session()
                if _HAS_RETRY:
                    retry = Retry(
                        total=2,                       # ≤2 retries — never hammer
                        backoff_factor=0.4,            # 0.4s, 0.8s (+ jitter)
                        status_forcelist=(429, 500, 502, 503, 504),
                        allowed_methods=frozenset(["GET"]),  # idempotent only
                        respect_retry_after_header=True,
                        raise_on_status=False,
                    )
                    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
                    s.mount("https://", adapter)
                    s.mount("http://", adapter)
                _session = s
    return _session


class CircuitOpenError(requests.exceptions.RequestException):
    """Raised (fast) when a provider's breaker is OPEN — subclasses
    RequestException so existing `except requests...`/`except Exception` blocks
    treat it like any other provider failure and fall back."""


def resilient_get(url: str, *, provider: str, **kwargs) -> requests.Response:
    """
    GET via the shared session, guarded by the provider's circuit breaker.
    Retries transient 5xx/429 (bounded) at the adapter layer. Raises on
    failure or open circuit — callers keep their own fallback handling.
    """
    br = get_breaker(provider)
    if not br.allow():
        record_provider_event(provider, success=False, error_type="CircuitOpen")
        raise CircuitOpenError(f"circuit_open:{provider}")
    started = time.perf_counter()
    try:
        r = get_session().get(url, **kwargs)
        operational = r.status_code < 500 and r.status_code != 429
        if operational:
            br.record_success()
        else:
            br.record_failure()
        record_provider_event(
            provider,
            success=operational,
            latency_ms=(time.perf_counter() - started) * 1000,
            error_type=None if operational else f"HTTP_{r.status_code}",
            status_code=r.status_code,
        )
        return r
    except Exception as exc:
        br.record_failure()
        record_provider_event(
            provider,
            success=False,
            latency_ms=(time.perf_counter() - started) * 1000,
            error_type=type(exc).__name__,
        )
        raise


def resilient_post(url: str, *, provider: str, **kwargs) -> requests.Response:
    """POST via the shared session + breaker. POSTs are NOT retried (not
    idempotent) — the breaker still provides fast-fail when the provider is down."""
    br = get_breaker(provider)
    if not br.allow():
        record_provider_event(provider, success=False, error_type="CircuitOpen")
        raise CircuitOpenError(f"circuit_open:{provider}")
    started = time.perf_counter()
    try:
        r = get_session().post(url, **kwargs)
        operational = r.status_code < 500 and r.status_code != 429
        if operational:
            br.record_success()
        else:
            br.record_failure()
        record_provider_event(
            provider,
            success=operational,
            latency_ms=(time.perf_counter() - started) * 1000,
            error_type=None if operational else f"HTTP_{r.status_code}",
            status_code=r.status_code,
        )
        return r
    except Exception as exc:
        br.record_failure()
        record_provider_event(
            provider,
            success=False,
            latency_ms=(time.perf_counter() - started) * 1000,
            error_type=type(exc).__name__,
        )
        raise
