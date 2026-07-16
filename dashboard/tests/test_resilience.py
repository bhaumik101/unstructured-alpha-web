"""Unit tests for utils.resilience circuit breaker (pure logic, no network)."""
import time

from utils.resilience import CircuitBreaker, get_breaker, get_session


def test_breaker_closed_allows():
    b = CircuitBreaker("t", fail_max=3, reset_timeout=60)
    assert b.allow() is True
    assert b.state() == "closed"


def test_breaker_opens_after_fail_max():
    b = CircuitBreaker("t", fail_max=3, reset_timeout=60)
    for _ in range(3):
        b.record_failure()
    assert b.state() == "open"
    assert b.allow() is False  # fast-fail while open


def test_success_resets_failures():
    b = CircuitBreaker("t", fail_max=3, reset_timeout=60)
    b.record_failure()
    b.record_failure()
    b.record_success()
    assert b.state() == "closed"
    # needs full fail_max again to open
    b.record_failure()
    b.record_failure()
    assert b.state() == "closed"


def test_half_open_after_cooldown_then_recovers():
    b = CircuitBreaker("t", fail_max=2, reset_timeout=0.2)
    b.record_failure(); b.record_failure()
    assert b.allow() is False          # open
    time.sleep(0.25)
    assert b.allow() is True           # half-open trial permitted
    assert b.state() == "half_open"
    b.record_success()                 # trial succeeds
    assert b.state() == "closed"
    assert b.allow() is True


def test_half_open_trial_failure_reopens():
    b = CircuitBreaker("t", fail_max=2, reset_timeout=0.2)
    b.record_failure(); b.record_failure()
    time.sleep(0.25)
    assert b.allow() is True           # half-open
    b.record_failure()                 # trial fails → cooldown restarts
    assert b.allow() is False


def test_get_breaker_singleton_per_name():
    a = get_breaker("prov_x")
    c = get_breaker("prov_x")
    assert a is c


def test_shared_session_is_singleton_and_pooled():
    s1 = get_session()
    s2 = get_session()
    assert s1 is s2
    # adapters mounted for both schemes
    assert "https://" in s1.adapters and "http://" in s1.adapters
