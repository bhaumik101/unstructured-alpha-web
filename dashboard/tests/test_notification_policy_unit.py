"""User-scoped notification controls and server-side policy bounds."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import delete

from utils import db
from utils.notification_policy import (
    DEFAULT_POLICY,
    POLICY_PRESETS,
    get_notification_policy,
    save_notification_policy,
)


USER_A = 9851
USER_B = 9852


@pytest.fixture(autouse=True)
def _policies():
    db.init_db()
    now = datetime.now(timezone.utc).isoformat()
    with db.engine.begin() as conn:
        conn.execute(delete(db.notification_policies).where(
            db.notification_policies.c.user_id.in_((USER_A, USER_B))
        ))
        conn.execute(delete(db.users).where(db.users.c.id.in_((USER_A, USER_B))))
        conn.execute(db.users.insert(), [
            {"id": USER_A, "email": "policy-a@example.com", "password_hash": "test", "created_at": now,
             "email_verified": True, "subscription_tier": "pro"},
            {"id": USER_B, "email": "policy-b@example.com", "password_hash": "test", "created_at": now,
             "email_verified": True, "subscription_tier": "pro"},
        ])
    yield
    with db.engine.begin() as conn:
        conn.execute(delete(db.notification_policies).where(
            db.notification_policies.c.user_id.in_((USER_A, USER_B))
        ))
        conn.execute(delete(db.users).where(db.users.c.id.in_((USER_A, USER_B))))


def test_default_policy_is_bounded_and_non_mutating():
    first = get_notification_policy(USER_A)
    first["catalyst_max_items"] = 1
    assert get_notification_policy(USER_A) == DEFAULT_POLICY


def test_plain_language_presets_are_valid_and_progressively_bounded():
    assert set(POLICY_PRESETS) == {"essentials", "balanced", "active"}
    assert [POLICY_PRESETS[key]["catalyst_max_items"] for key in POLICY_PRESETS] == [2, 3, 4]
    for preset in POLICY_PRESETS.values():
        saved = save_notification_policy(USER_A, preset)
        assert saved == preset


def test_policy_is_private_and_updates_in_place():
    saved = save_notification_policy(USER_A, {
        "catalyst_horizon_days": 3,
        "catalyst_max_items": 2,
        "include_macro_events": False,
        "include_earnings": True,
        "plan_only": True,
        "review_reminders": False,
    })
    assert saved["catalyst_horizon_days"] == 3
    assert get_notification_policy(USER_A) == saved
    assert get_notification_policy(USER_B) == DEFAULT_POLICY

    updated = save_notification_policy(USER_A, {**saved, "catalyst_max_items": 1})
    assert updated["catalyst_max_items"] == 1
    with db.engine.begin() as conn:
        count = conn.execute(
            db.notification_policies.select().where(db.notification_policies.c.user_id == USER_A)
        ).fetchall()
    assert len(count) == 1


@pytest.mark.parametrize("values", [
    {"catalyst_horizon_days": 2, "catalyst_max_items": 2},
    {"catalyst_horizon_days": 7, "catalyst_max_items": 0},
    {"catalyst_horizon_days": 7, "catalyst_max_items": 5},
])
def test_invalid_limits_are_rejected(values):
    with pytest.raises(ValueError):
        save_notification_policy(USER_A, values)
