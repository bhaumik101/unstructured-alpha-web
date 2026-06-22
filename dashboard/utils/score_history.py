# utils/score_history.py
# Unstructured Alpha — Historical Score Snapshots
#
# WHY THIS MODULE EXISTS: every score on this site, before today, was a
# pure point-in-time computation -- nothing remembered what a ticker's
# score was yesterday or last month. That blocks three things the
# 2026-06-22 roadmap calls for: a Score History chart on Ticker Deep
# Dive, a future public track-record page, and alert deltas compared
# against a real stored value instead of whatever the last alert
# happened to see. This module is the foundation all three sit on.
#
# NOT user-scoped, deliberately: a ticker's Confluence Score at a given
# moment is the same number for every visitor, so utils/db.py's
# score_snapshots table is keyed by (ticker, day), not by user.
#
# NO BACKGROUND SCHEDULER: this is a Streamlit app with no cron. History
# accumulates only for tickers someone actually opens on Ticker Deep
# Dive, upserted at view time -- organic, traffic-driven coverage, not a
# guaranteed daily record across the whole signal universe. That's a
# real, honest limitation worth stating plainly wherever this data is
# displayed, not glossed over.

from datetime import datetime, timezone

from sqlalchemy import select

from utils import db
from utils.db import score_snapshots, upsert_stmt
from utils.lead_time_research import get_sector_peers


def record_score_snapshot(ticker: str, score: float, case: str, conviction: str) -> None:
    """
    Upsert today's score snapshot for `ticker`. Safe to call on every
    Ticker Deep Dive page view -- the unique (ticker, snapshot_date)
    constraint means a second visit later the same day OVERWRITES the
    same row with the latest score (intentional: today's most recent
    computation is the one worth keeping, not the first of the day),
    rather than creating duplicate rows.
    """
    ticker = ticker.upper().strip()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_iso = datetime.now(timezone.utc).isoformat()

    stmt = upsert_stmt(score_snapshots, ["ticker", "snapshot_date"]).values(
        ticker=ticker, snapshot_date=today, score=score, case=case,
        conviction=conviction, created_at=now_iso,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["ticker", "snapshot_date"],
        set_={"score": score, "case": case, "conviction": conviction, "created_at": now_iso},
    )
    with db.engine.begin() as conn:
        conn.execute(stmt)


def get_score_history(ticker: str, days: int = 180) -> list[dict]:
    """
    Return up to `days` worth of snapshot rows for `ticker`, oldest first
    -- exactly what's actually been recorded, no interpolation or
    backfilling of missing days. A ticker nobody has viewed recently (or
    ever) legitimately returns an empty or sparse list; callers must
    treat that as "not enough history yet," never synthesize a fake trend.
    """
    ticker = ticker.upper().strip()
    with db.engine.begin() as conn:
        rows = conn.execute(
            select(score_snapshots)
            .where(score_snapshots.c.ticker == ticker)
            .order_by(score_snapshots.c.snapshot_date.desc())
            .limit(days)
        ).mappings().all()
    return [dict(r) for r in reversed(rows)]


def compute_sector_percentile(ticker: str, score: float, max_peers: int = 6) -> dict:
    """
    Where `score` (the ticker's CURRENT, just-computed score) ranks
    against its sector peers' most recently RECORDED scores.

    Deliberately built on the snapshot history above rather than live-
    scoring every peer on every page view: computing a peer's full
    Confluence Score means re-running its own signal/price/insider/13F
    fetch pipeline, and doing that for up to 6 peers on every single
    ticker view would multiply this page's real cost several times over
    for a "nice to have" comparison number. Reusing whatever's already
    been recorded is free (a few indexed DB reads) and ties naturally
    into the same organic, traffic-driven history this module already
    builds.

    Honest tradeoff this creates, stated plainly rather than hidden: a
    peer's score here is whatever it was AS OF that peer's last view, not
    a live number -- two peers compared "at the same time" may actually
    be several days or weeks apart. `peer_scores` always includes each
    peer's `as_of` date so a caller (or the UI) can show that, not just
    the number.
    """
    peers = get_sector_peers(ticker, max_peers=max_peers)
    if not peers:
        return {"error": "No sector peers found for this ticker", "n_peers": 0}

    peer_scores = []
    for peer in peers:
        hist = get_score_history(peer, days=30)
        if hist:
            peer_scores.append({"ticker": peer, "score": hist[-1]["score"], "as_of": hist[-1]["snapshot_date"]})

    if not peer_scores:
        return {
            "error": "None of this ticker's sector peers have a recent recorded score yet",
            "n_peers": 0,
        }

    all_scores = [p["score"] for p in peer_scores] + [score]
    rank = sum(1 for s in all_scores if s <= score)
    percentile = round(100.0 * rank / len(all_scores), 1)
    sector_avg = round(sum(p["score"] for p in peer_scores) / len(peer_scores), 1)

    return {
        "error": None,
        "percentile": percentile,
        "n_peers": len(peer_scores),
        "peer_scores": peer_scores,
        "sector_avg": sector_avg,
    }
