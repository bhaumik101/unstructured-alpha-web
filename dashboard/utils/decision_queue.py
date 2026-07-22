"""Evidence-only Pro Decision Queue and user-scoped triage persistence."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable

from sqlalchemy import or_, select

from utils.db import decision_queue_states, engine, score_snapshots, upsert_stmt


VALID_STATUSES = {"open", "watching", "done", "snoozed"}
SCORE_MOVE_THRESHOLD = 8.0
CONCENTRATION_THRESHOLD = 20.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value or "")[:10])
    except ValueError:
        return None


def load_score_changes(
    tickers: Iterable[str], *, days: int = 7, as_of: date | None = None
) -> dict[str, dict]:
    """Return honest persisted score movement; never calculate or estimate it."""
    symbols = sorted({str(t).upper().strip() for t in tickers if str(t).strip()})
    if not symbols:
        return {}
    end = as_of or datetime.now(timezone.utc).date()
    start = end - timedelta(days=max(1, int(days)))
    with engine.begin() as conn:
        rows = conn.execute(
            select(
                score_snapshots.c.ticker,
                score_snapshots.c.snapshot_date,
                score_snapshots.c.score,
            )
            .where(
                score_snapshots.c.ticker.in_(symbols),
                score_snapshots.c.snapshot_date >= start.isoformat(),
                score_snapshots.c.snapshot_date <= end.isoformat(),
                or_(
                    score_snapshots.c.score_kind == "full",
                    score_snapshots.c.score_kind.is_(None),
                ),
            )
            .order_by(
                score_snapshots.c.ticker,
                score_snapshots.c.snapshot_date.asc(),
                score_snapshots.c.id.asc(),
            )
        ).mappings().all()

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row["ticker"]).upper(), []).append(dict(row))
    return {
        ticker: {
            "from_score": round(float(values[0]["score"]), 1),
            "to_score": round(float(values[-1]["score"]), 1),
            "delta": round(float(values[-1]["score"]) - float(values[0]["score"]), 1),
            "from_date": values[0]["snapshot_date"],
            "to_date": values[-1]["snapshot_date"],
            "observations": len(values),
        }
        for ticker, values in grouped.items()
        if values
    }


def _trigger(
    kind: str,
    priority: float,
    title: str,
    detail: str,
    action: str,
    route: str,
) -> dict:
    return {
        "kind": kind,
        "priority": float(priority),
        "title": title,
        "detail": detail,
        "action": action,
        "route": route,
    }


def _fingerprint(item: dict) -> str:
    payload = {
        "ticker": item["ticker"],
        "score": item.get("score"),
        "snapshot_date": item.get("snapshot_date"),
        "weight_pct": item.get("weight_pct"),
        "triggers": [
            {"kind": row["kind"], "detail": row["detail"]}
            for row in item.get("triggers", [])
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_decision_queue(
    evidence: Iterable[dict],
    *,
    score_changes: dict[str, dict] | None = None,
    theses: Iterable[dict] | None = None,
    earnings: dict[str, dict | None] | None = None,
    today: date | None = None,
) -> list[dict]:
    """Rank review needs from recorded facts without producing trade advice."""
    day = today or datetime.now(timezone.utc).date()
    changes = score_changes or {}
    earnings_map = earnings or {}
    thesis_map = {
        str(row.get("ticker", "")).upper(): dict(row)
        for row in (theses or [])
        if str(row.get("ticker", "")).strip()
    }
    items: list[dict] = []

    for raw in evidence or []:
        ticker = str(raw.get("ticker", "")).upper().strip()
        if not ticker:
            continue
        snapshot = raw.get("snapshot") or {}
        score_kind = snapshot.get("score_kind")
        score_value = snapshot.get("score") if score_kind in (None, "full") else None
        score = round(float(score_value), 1) if score_value is not None else None
        snapshot_day = _as_date(snapshot.get("snapshot_date"))
        score_is_stale = bool(snapshot_day and (day - snapshot_day).days > 7)
        weight = round(max(0.0, float(raw.get("weight_pct") or 0)), 2)
        triggers: list[dict] = []

        if score is None:
            triggers.append(_trigger(
                "coverage_gap", 94,
                "Score evidence is unavailable",
                "No trustworthy persisted Confluence Score is available for this position.",
                "Open the ticker and review its coverage",
                "ticker",
            ))
        else:
            if score_is_stale:
                triggers.append(_trigger(
                    "stale_evidence", 90,
                    "Score evidence is stale",
                    f"The latest persisted full score is dated {snapshot.get('snapshot_date')}; it is not treated as current.",
                    "Refresh the ticker evidence",
                    "ticker",
                ))
            movement = changes.get(ticker) or {}
            delta = movement.get("delta")
            if delta is not None and abs(float(delta)) >= SCORE_MOVE_THRESHOLD:
                direction = "rose" if float(delta) > 0 else "fell"
                triggers.append(_trigger(
                    "score_move", 88 + min(abs(float(delta)), 12),
                    "Material score move",
                    f"The persisted Confluence Score {direction} {abs(float(delta)):.1f} points "
                    f"from {movement.get('from_date')} to {movement.get('to_date')}.",
                    "Review the evidence behind the move",
                    "ticker",
                ))

        event = earnings_map.get(ticker)
        if event:
            days_until = int(event.get("days_until", 999))
            if 0 <= days_until <= 21:
                priority = 97 if days_until <= 3 else (84 if days_until <= 10 else 70)
                when = "today" if days_until == 0 else (
                    "tomorrow" if days_until == 1 else f"in {days_until} days"
                )
                estimate = " The provider marks this date as provisional." if event.get("is_estimate") else ""
                triggers.append(_trigger(
                    "earnings", priority,
                    "Earnings event risk",
                    f"Earnings are expected {when}.{estimate}",
                    "Prepare the pre-earnings thesis review",
                    "thesis",
                ))

        thesis = thesis_map.get(ticker)
        if thesis and str(thesis.get("status", "")).lower() == "active":
            stance = str(thesis.get("stance", "Neutral")).title()
            conflicts = (
                score is not None
                and not score_is_stale
                and ((stance == "Bullish" and score <= 35) or (stance == "Bearish" and score >= 65))
            )
            if conflicts:
                triggers.append(_trigger(
                    "thesis_conflict", 93,
                    "Thesis and evidence conflict",
                    f"Your active {stance.lower()} thesis conflicts with the latest recorded score of {score:.1f}.",
                    "Review the invalidation rule",
                    "thesis",
                ))

            created = _as_date(thesis.get("created_at"))
            horizon_weeks = max(1, int(thesis.get("horizon_weeks") or 12))
            if created and day >= created + timedelta(weeks=horizon_weeks):
                triggers.append(_trigger(
                    "thesis_due", 74,
                    "Thesis horizon reached",
                    f"The recorded {horizon_weeks}-week thesis horizon has elapsed.",
                    "Record the outcome or extend the thesis",
                    "thesis",
                ))

        if str(raw.get("source") or "") == "portfolio" and weight >= CONCENTRATION_THRESHOLD:
            triggers.append(_trigger(
                "concentration", 66 + min((weight - CONCENTRATION_THRESHOLD) / 2, 14),
                "Position concentration",
                f"This holding represents {weight:.1f}% of the saved portfolio.",
                "Review portfolio concentration",
                "portfolio",
            ))

        if not triggers:
            continue
        triggers.sort(key=lambda row: (-row["priority"], row["kind"]))
        lead = triggers[0]
        priority = min(
            100.0,
            float(lead["priority"]) + min(8.0, 2.0 * (len(triggers) - 1)) + min(4.0, weight / 10),
        )
        item = {
            "item_key": ticker,
            "ticker": ticker,
            "priority": round(priority, 1),
            "severity": "urgent" if priority >= 92 else ("high" if priority >= 78 else "review"),
            "headline": lead["title"],
            "why_now": lead["detail"],
            "next_action": lead["action"],
            "route": lead["route"],
            "score": score,
            "case": str(snapshot.get("case") or "UNAVAILABLE").upper(),
            "snapshot_date": snapshot.get("snapshot_date"),
            "weight_pct": weight,
            "source": raw.get("source") or "watchlist",
            "triggers": triggers,
        }
        item["evidence_hash"] = _fingerprint(item)
        items.append(item)

    items.sort(key=lambda row: (-row["priority"], -row["weight_pct"], row["ticker"]))
    return items


def list_queue_states(user_id: int) -> dict[str, dict]:
    with engine.begin() as conn:
        rows = conn.execute(
            select(decision_queue_states).where(
                decision_queue_states.c.user_id == int(user_id)
            )
        ).mappings().all()
    return {str(row["item_key"]): dict(row) for row in rows}


def apply_queue_states(
    items: Iterable[dict], states: dict[str, dict], *, today: date | None = None
) -> list[dict]:
    """Apply triage only to identical evidence; changed evidence reopens work."""
    day = today or datetime.now(timezone.utc).date()
    output: list[dict] = []
    for source in items:
        item = dict(source)
        saved = states.get(str(item["item_key"])) or {}
        same_evidence = saved.get("evidence_hash") == item.get("evidence_hash")
        status = str(saved.get("status") or "open") if same_evidence else "open"
        if status == "snoozed":
            until = _as_date(saved.get("snoozed_until"))
            if until is None or until < day:
                status = "open"
        item["status"] = status if status in VALID_STATUSES else "open"
        item["snoozed_until"] = saved.get("snoozed_until") if same_evidence else None
        item["note"] = saved.get("note") if same_evidence else None
        output.append(item)
    return output


def set_queue_state(
    user_id: int,
    item_key: str,
    evidence_hash: str,
    status: str,
    *,
    snoozed_until: date | str | None = None,
    note: str = "",
) -> None:
    normalized = str(status).lower().strip()
    if normalized not in VALID_STATUSES:
        raise ValueError("Invalid decision queue status.")
    key = str(item_key).upper().strip()
    if not key or len(key) > 32:
        raise ValueError("Invalid decision queue item key.")
    until = _as_date(snoozed_until)
    if normalized == "snoozed" and until is None:
        raise ValueError("A snooze date is required.")
    clean_note = str(note or "").strip()[:1000]
    now = _now()
    stmt = upsert_stmt(decision_queue_states, ["user_id", "item_key"]).values(
        user_id=int(user_id),
        item_key=key,
        evidence_hash=str(evidence_hash),
        status=normalized,
        snoozed_until=until.isoformat() if until else None,
        note=clean_note or None,
        created_at=now,
        updated_at=now,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "item_key"],
        set_={
            "evidence_hash": str(evidence_hash),
            "status": normalized,
            "snoozed_until": until.isoformat() if until else None,
            "note": clean_note or None,
            "updated_at": now,
        },
    )
    with engine.begin() as conn:
        conn.execute(stmt)
