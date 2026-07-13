# utils/universe.py
# Unstructured Alpha — Growing Ticker Universe
#
# WHY THIS MODULE EXISTS: the tracked universe used to be exactly utils.config
# TICKERS — a hand-curated dict baked into code. That means the only way the
# universe grows is a developer editing a file. But the product should get more
# useful the more it's used: every stock a real user cares enough to watchlist
# should join the universe (so it's pre-warmed, counted, and screenable), and
# we should proactively seed the big names in the industries we cover so their
# data pulls up instantly for the next customer.
#
# This module is that growth layer. It's backed by the db.dynamic_universe
# table (runtime-writable, unlike code) and always MERGES with the static
# TICKERS so nothing curated is ever lost. Every write is best-effort and
# defensive — the universe growing is a nice-to-have that must never break the
# watchlist add or the page it's called from.
#
# The pure merge/normalise helpers have no DB dependency and are unit-tested;
# the DB reads/writes are thin wrappers around them.

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from utils.config import TICKERS


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_ticker(ticker: str) -> str:
    return (ticker or "").upper().strip()


def resolve_meta(ticker: str) -> dict:
    """
    Best-effort (name, sector) for a ticker. Prefers the curated static
    universe; falls back to yfinance; falls back to bare defaults. Never raises.
    """
    t = normalize_ticker(ticker)
    meta = TICKERS.get(t)
    if meta:
        return {"name": meta.get("name", t), "sector": meta.get("sector", "")}
    try:
        import yfinance as yf
        info = yf.Ticker(t).info or {}
        return {
            "name": info.get("longName") or info.get("shortName") or t,
            "sector": info.get("sector", "") or "",
        }
    except Exception:
        return {"name": t, "sector": ""}


def merge_universe(static_tickers, dynamic_tickers) -> list[str]:
    """
    Pure merge: the union of the static universe and the dynamic additions,
    normalised and de-duplicated, sorted. static_tickers may be a dict (keys)
    or an iterable; dynamic_tickers is an iterable of ticker strings.
    """
    keys = static_tickers.keys() if hasattr(static_tickers, "keys") else static_tickers
    out = {normalize_ticker(t) for t in keys if normalize_ticker(t)}
    out |= {normalize_ticker(t) for t in (dynamic_tickers or []) if normalize_ticker(t)}
    return sorted(out)


# ─────────────────────────────────────────────────────────────────────────────
# DB-backed operations (thin, defensive wrappers)
# ─────────────────────────────────────────────────────────────────────────────

def add_to_universe(ticker: str, source: str = "watchlist",
                    name: Optional[str] = None, sector: Optional[str] = None) -> bool:
    """
    Add (or refresh) a ticker in the dynamic universe. Idempotent via the unique
    ticker constraint. Returns True on a successful write, False otherwise.
    Best-effort: any DB/network hiccup is swallowed — growing the universe must
    never break the caller (a watchlist add, a page view, a cron).
    """
    t = normalize_ticker(ticker)
    if not t or not t.replace(".", "").replace("-", "").isalnum() or len(t) > 16:
        return False
    try:
        from utils import db
        from utils.db import dynamic_universe, upsert_stmt
        if name is None or sector is None:
            meta = resolve_meta(t)
            name = name or meta["name"]
            sector = sector or meta["sector"]
        stmt = upsert_stmt(dynamic_universe, ["ticker"]).values(
            ticker=t, name=name, sector=sector, source=source, added_at=_now_iso(),
        )
        # Refresh name/sector on conflict, but keep the ORIGINAL source (a
        # user-watchlisted name shouldn't be relabelled "daily" by the seeder).
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker"],
            set_={"name": name, "sector": sector},
        )
        with db.engine.begin() as conn:
            conn.execute(stmt)
        return True
    except Exception:
        return False


def get_dynamic_universe() -> list[dict]:
    """All rows from the dynamic universe, or [] on any error."""
    try:
        from sqlalchemy import select
        from utils import db
        from utils.db import dynamic_universe
        with db.engine.begin() as conn:
            rows = conn.execute(
                select(dynamic_universe).order_by(dynamic_universe.c.ticker)
            ).mappings().all()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_full_universe() -> list[str]:
    """
    The merged tracked universe: static TICKERS ∪ dynamic additions. Falls back
    to just the static universe if the dynamic table can't be read.
    """
    dyn = [r.get("ticker") for r in get_dynamic_universe()]
    return merge_universe(TICKERS, dyn)


def universe_size() -> dict:
    """Counts for display: static, dynamic-only additions, and the total."""
    static_keys = {normalize_ticker(t) for t in TICKERS.keys()}
    dyn = {normalize_ticker(r.get("ticker")) for r in get_dynamic_universe()}
    dyn_only = dyn - static_keys
    return {"static": len(static_keys), "added": len(dyn_only), "total": len(static_keys | dyn)}
