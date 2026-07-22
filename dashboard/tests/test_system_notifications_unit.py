"""Per-user clearing behavior for the shared system-notification feed."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine

from utils import db
from utils.prediction_log import (
    clear_notifications,
    get_recent_notifications,
    get_unread_notification_count,
)


@pytest.fixture(autouse=True)
def _isolated_database(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "IS_SQLITE", True)
    db.metadata.create_all(engine)
    now = datetime.now(timezone.utc).isoformat()
    with engine.begin() as conn:
        for user_id in (7101, 7102):
            conn.execute(db.users.insert().values(
                id=user_id,
                email=f"user-{user_id}@example.com",
                password_hash="unused",
                created_at=now,
                email_verified=True,
            ))
        for index in range(3):
            conn.execute(db.system_notifications.insert().values(
                notif_type="convergence",
                title=f"Signal {index}",
                body="Evidence changed.",
                ticker="SPY",
                direction="bull",
                created_at=now,
            ))
    yield


def test_clear_is_private_and_future_notifications_reappear():
    assert len(get_recent_notifications(user_id=7101)) == 3
    assert len(get_recent_notifications(user_id=7102)) == 3

    assert clear_notifications(7101)

    assert get_recent_notifications(user_id=7101) == []
    assert get_unread_notification_count(7101) == 0
    assert len(get_recent_notifications(user_id=7102)) == 3
    assert get_unread_notification_count(7102) == 3

    with db.engine.begin() as conn:
        conn.execute(db.system_notifications.insert().values(
            notif_type="near_flip",
            title="New event",
            body="This happened after the clear action.",
            ticker="MSFT",
            direction=None,
            created_at=datetime.now(timezone.utc).isoformat(),
        ))

    visible = get_recent_notifications(user_id=7101)
    assert [item["title"] for item in visible] == ["New event"]
    assert get_unread_notification_count(7101) == 1


def test_clear_can_be_repeated_safely():
    assert clear_notifications(7101)
    assert clear_notifications(7101)
    assert get_recent_notifications(user_id=7101) == []
