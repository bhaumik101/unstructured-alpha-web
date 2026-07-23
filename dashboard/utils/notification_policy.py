"""Validated user controls for bounded proactive intelligence delivery."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from utils.db import engine, notification_policies, upsert_stmt


ALLOWED_HORIZONS = (1, 3, 7)
MIN_ITEMS = 1
MAX_ITEMS = 4
DEFAULT_POLICY = {
    "catalyst_horizon_days": 7,
    "catalyst_max_items": 4,
    "include_macro_events": True,
    "include_earnings": True,
    "plan_only": False,
    "review_reminders": True,
}
POLICY_PRESETS = {
    "essentials": {
        **DEFAULT_POLICY,
        "catalyst_horizon_days": 3,
        "catalyst_max_items": 2,
    },
    "balanced": {
        **DEFAULT_POLICY,
        "catalyst_horizon_days": 7,
        "catalyst_max_items": 3,
    },
    "active": {
        **DEFAULT_POLICY,
        "catalyst_horizon_days": 7,
        "catalyst_max_items": 4,
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(values: dict | None) -> dict:
    values = values or {}
    try:
        horizon = int(values.get("catalyst_horizon_days", DEFAULT_POLICY["catalyst_horizon_days"]))
        max_items = int(values.get("catalyst_max_items", DEFAULT_POLICY["catalyst_max_items"]))
    except (TypeError, ValueError) as exc:
        raise ValueError("Notification limits must be whole numbers.") from exc
    if horizon not in ALLOWED_HORIZONS:
        raise ValueError("Catalyst lead time must be 1, 3, or 7 days.")
    if not MIN_ITEMS <= max_items <= MAX_ITEMS:
        raise ValueError(f"Catalyst item limit must be between {MIN_ITEMS} and {MAX_ITEMS}.")
    return {
        "catalyst_horizon_days": horizon,
        "catalyst_max_items": max_items,
        "include_macro_events": bool(values.get("include_macro_events", True)),
        "include_earnings": bool(values.get("include_earnings", True)),
        "plan_only": bool(values.get("plan_only", False)),
        "review_reminders": bool(values.get("review_reminders", True)),
    }


def get_notification_policy(user_id: int) -> dict:
    with engine.begin() as conn:
        row = conn.execute(
            select(notification_policies).where(notification_policies.c.user_id == int(user_id))
        ).mappings().first()
    if not row:
        return dict(DEFAULT_POLICY)
    return _normalize(dict(row))


def save_notification_policy(user_id: int, values: dict) -> dict:
    normalized = _normalize(values)
    now = _now()
    payload = {
        "user_id": int(user_id),
        **normalized,
        "created_at": now,
        "updated_at": now,
    }
    stmt = upsert_stmt(notification_policies, ["user_id"]).values(**payload)
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id"],
        set_={key: value for key, value in payload.items() if key not in {"user_id", "created_at"}},
    )
    with engine.begin() as conn:
        conn.execute(stmt)
    return normalized
