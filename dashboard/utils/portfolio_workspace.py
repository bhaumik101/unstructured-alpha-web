"""Persistent, user-scoped portfolio holdings for Portfolio Intelligence."""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import delete, select

from utils.db import engine, portfolio_holdings, portfolios, upsert_stmt
from utils.guards import MAX_PORTFOLIO_HOLDINGS


DEFAULT_PORTFOLIO_NAME = "My Portfolio"
_TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,14}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_ticker(value: object) -> str:
    ticker = str(value or "").upper().strip().lstrip("$")
    if not _TICKER_RE.fullmatch(ticker):
        raise ValueError(f"Invalid ticker: {value!s}")
    return ticker


def normalize_holdings(rows: Iterable[dict], *, limit: int = MAX_PORTFOLIO_HOLDINGS) -> list[dict]:
    """Deduplicate positions and normalize positive weights to exactly 100%."""
    deduped: dict[str, dict] = {}
    for row in rows or []:
        ticker = _normalize_ticker(row.get("ticker"))
        raw_weight = row.get("weight_pct", row.get("weight"))
        weight = None if raw_weight in (None, "") else float(raw_weight)
        if weight is not None and (not math.isfinite(weight) or weight < 0):
            raise ValueError(f"Weight for {ticker} must be a positive number.")
        shares = row.get("shares")
        cost_basis = row.get("cost_basis")
        shares = float(shares) if shares not in (None, "") else None
        cost_basis = float(cost_basis) if cost_basis not in (None, "") else None
        if shares is not None and (not math.isfinite(shares) or shares < 0):
            raise ValueError(f"Shares for {ticker} must be a positive number.")
        if cost_basis is not None and (not math.isfinite(cost_basis) or cost_basis < 0):
            raise ValueError(f"Cost basis for {ticker} must be a positive number.")
        deduped[ticker] = {
            "ticker": ticker,
            "weight_pct": weight,
            "shares": shares,
            "cost_basis": cost_basis,
        }

    positions = list(deduped.values())[: max(1, int(limit))]
    if not positions:
        return []

    specified = [p["weight_pct"] for p in positions if p["weight_pct"] is not None and p["weight_pct"] > 0]
    fallback = (sum(specified) / len(specified)) if specified else 1.0
    raw = [p["weight_pct"] if p["weight_pct"] is not None and p["weight_pct"] > 0 else fallback for p in positions]
    total = sum(raw)
    for index, position in enumerate(positions):
        position["weight_pct"] = round(raw[index] * 100.0 / total, 4)
    # Make the persisted total deterministic despite rounding.
    positions[-1]["weight_pct"] = round(
        positions[-1]["weight_pct"] + (100.0 - sum(p["weight_pct"] for p in positions)), 4
    )
    return positions


def parse_holdings_text(
    text: str,
    *,
    valid_symbols: set[str] | None = None,
    limit: int = MAX_PORTFOLIO_HOLDINGS,
) -> tuple[list[dict], list[str]]:
    """Parse ``TICKER, weight`` or ``TICKER weight`` lines for bulk import."""
    rows: list[dict] = []
    rejected: list[str] = []
    allowed = {s.upper() for s in valid_symbols} if valid_symbols is not None else None
    for source_line in (text or "").splitlines():
        line = source_line.strip()
        if not line:
            continue
        parts = [part for part in re.split(r"[,\t\s]+", line) if part]
        try:
            ticker = _normalize_ticker(parts[0])
            if allowed is not None and ticker not in allowed:
                raise ValueError
            weight = float(parts[1].rstrip("%")) if len(parts) > 1 else None
            rows.append({"ticker": ticker, "weight_pct": weight})
        except (ValueError, IndexError):
            rejected.append(line)
    return normalize_holdings(rows, limit=limit), rejected


def get_or_create_default_portfolio(user_id: int) -> dict:
    """Return the user's stable default portfolio, creating it idempotently."""
    user_id = int(user_id)
    now = _now()
    stmt = upsert_stmt(portfolios, ["user_id", "name"]).values(
        user_id=user_id,
        name=DEFAULT_PORTFOLIO_NAME,
        is_default=1,
        created_at=now,
        updated_at=now,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "name"],
        set_={"is_default": 1},
    )
    with engine.begin() as conn:
        conn.execute(stmt)
        row = conn.execute(
            select(portfolios).where(
                portfolios.c.user_id == user_id,
                portfolios.c.name == DEFAULT_PORTFOLIO_NAME,
            )
        ).mappings().one()
    return dict(row)


def get_default_holdings(user_id: int, *, create: bool = False) -> list[dict]:
    """Read only the requesting user's default portfolio positions."""
    user_id = int(user_id)
    with engine.begin() as conn:
        portfolio = conn.execute(
            select(portfolios.c.id).where(
                portfolios.c.user_id == user_id,
                portfolios.c.is_default == 1,
            ).order_by(portfolios.c.id).limit(1)
        ).first()
    if not portfolio:
        if not create:
            return []
        portfolio_id = get_or_create_default_portfolio(user_id)["id"]
    else:
        portfolio_id = portfolio[0]
    with engine.begin() as conn:
        rows = conn.execute(
            select(portfolio_holdings)
            .where(portfolio_holdings.c.portfolio_id == portfolio_id)
            .order_by(portfolio_holdings.c.weight_pct.desc(), portfolio_holdings.c.ticker)
        ).mappings().all()
    return [dict(row) for row in rows]


def replace_default_holdings(user_id: int, rows: Iterable[dict]) -> list[dict]:
    """Atomically replace a user's default portfolio with validated positions."""
    normalized = normalize_holdings(rows)
    portfolio = get_or_create_default_portfolio(int(user_id))
    now = _now()
    with engine.begin() as conn:
        conn.execute(
            delete(portfolio_holdings).where(portfolio_holdings.c.portfolio_id == portfolio["id"])
        )
        if normalized:
            conn.execute(
                portfolio_holdings.insert(),
                [
                    {
                        "portfolio_id": portfolio["id"],
                        **position,
                        "created_at": now,
                        "updated_at": now,
                    }
                    for position in normalized
                ],
            )
        conn.execute(
            portfolios.update()
            .where(portfolios.c.id == portfolio["id"])
            .values(updated_at=now)
        )
    return get_default_holdings(int(user_id))
