# utils/db.py
# Unstructured Alpha — Database Engine + Schema
#
# Single source of truth for the SQL backend, built on SQLAlchemy Core
# (not the ORM -- this app's data model is simple enough that explicit
# Table objects + hand-written queries are easier to reason about than an
# ORM's session/identity-map machinery, and easier for a reviewer to audit
# against the actual SQL that runs).
#
# Why SQLAlchemy at all, instead of raw sqlite3/psycopg2: this app needs to
# run against TWO different databases depending on environment --
# Postgres in production (chosen explicitly: Streamlit Community Cloud has
# no persistent disk, so account/watchlist data has to live in a real
# hosted database, not a local file) and SQLite for local development and
# tests (no Postgres server needed to run `streamlit run app.py` or pytest
# on a laptop). Hand-writing raw SQL for both dialects (AUTOINCREMENT vs
# SERIAL, different upsert syntax, etc.) is a real source of bugs that
# would only surface in production against a database I can't directly
# test against here. SQLAlchemy's Core layer abstracts those dialect
# differences so the same Python code runs correctly against either.
#
# Connection string resolution:
#   1. UNSTRUCTURED_ALPHA_DATABASE_URL environment variable -- checked
#      FIRST, deliberately, ahead of st.secrets. This is what tests/conftest.py
#      sets to a throwaway SQLite file before any test runs. Caught live,
#      not assumed: with secrets checked first, running pytest on a machine
#      that has a real .streamlit/secrets.toml configured (i.e. any
#      developer's actual laptop, not just a sandbox without network access)
#      would silently connect to and write fake test users/alerts into the
#      REAL production Neon database instead of the intended test DB --
#      the only reason this didn't already happen unnoticed is that it was
#      run somewhere with no network route to Neon, which surfaced it as a
#      connection error instead of silent data pollution. An explicit env
#      var override is a narrower, more deliberate signal than whatever
#      happens to be sitting in a local secrets.toml, so it must win.
#   2. st.secrets["DATABASE_URL"] if running under Streamlit with that
#      secret configured (the production path -- a Postgres URL from
#      Neon/Supabase/Railway, set in Streamlit Community Cloud's app
#      settings, never committed to the repo). Streamlit Cloud itself never
#      sets the env var above, so this remains the real production path.
#   3. A local SQLite file at ~/.unstructured_alpha/data/app.db (the
#      existing local-dev default -- and the same reasoning as before for
#      WHY it lives outside the project folder: a cloud-synced project
#      directory causes real SQLite disk I/O errors, confirmed live).

import os

import streamlit as st
from sqlalchemy import (
    create_engine, inspect, text, MetaData, Table, Column, Integer, String, Float, Text, Boolean,
    ForeignKey, UniqueConstraint, select, insert, update, delete, func,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

_LOCAL_DB_DIR = os.path.join(os.path.expanduser("~"), ".unstructured_alpha", "data")
_LOCAL_DB_PATH = os.path.join(_LOCAL_DB_DIR, "app.db")


def _resolve_database_url() -> str:
    env_url = os.environ.get("UNSTRUCTURED_ALPHA_DATABASE_URL")
    if env_url:
        return env_url

    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass  # st.secrets raises if no secrets.toml exists at all -- fine, fall through

    os.makedirs(_LOCAL_DB_DIR, exist_ok=True)
    return f"sqlite:///{_LOCAL_DB_PATH}"


DATABASE_URL = _resolve_database_url()
IS_SQLITE = DATABASE_URL.startswith("sqlite")

_engine_kwargs = {"connect_args": {"check_same_thread": False}} if IS_SQLITE else {"pool_pre_ping": True}
engine = create_engine(DATABASE_URL, **_engine_kwargs)

metadata = MetaData()

users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), nullable=False, unique=True),
    Column("password_hash", Text, nullable=False),
    Column("created_at", String(64), nullable=False),
    # Email verification (added 2026-06-21, after accounts already existed
    # in the running local DB -- see _migrate_users_table() below for why
    # this needs an explicit ALTER TABLE step, not just create_all()).
    Column("email_verified", Boolean, nullable=False, server_default="0"),
    Column("verification_code_hash", Text),
    Column("verification_code_expires_at", String(64)),
)

watchlist = Table(
    "watchlist", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("ticker", String(16), nullable=False),
    Column("score_bull_threshold", Float, nullable=False, server_default="65.0"),
    Column("score_bear_threshold", Float, nullable=False, server_default="35.0"),
    Column("price_move_pct_threshold", Float, nullable=False, server_default="5.0"),
    Column("added_at", String(64), nullable=False),
    UniqueConstraint("user_id", "ticker", name="uq_watchlist_user_ticker"),
)

alert_state = Table(
    "alert_state", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("ticker", String(16), nullable=False),
    Column("last_score", Float),
    Column("last_price", Float),
    Column("last_52w_high", Float),
    Column("last_52w_low", Float),
    Column("last_insider_status", String(32)),
    Column("last_short_interest_status", String(32)),
    Column("last_13f_status", String(32)),
    Column("last_checked_at", String(64)),
    UniqueConstraint("user_id", "ticker", name="uq_alert_state_user_ticker"),
)

alerts = Table(
    "alerts", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("ticker", String(16), nullable=False),
    Column("alert_type", String(32), nullable=False),
    Column("direction", String(16)),
    Column("message", Text, nullable=False),
    Column("created_at", String(64), nullable=False),
    Column("is_read", Integer, nullable=False, server_default="0"),
)


def _migrate_users_table() -> None:
    """
    metadata.create_all() only creates tables that don't exist yet -- it
    does NOT add new columns to a table that's already there. The
    email_verified / verification_code_* columns were added to the `users`
    Table definition above AFTER real accounts already existed in the
    running local database (and will exist in production once real users
    sign up there too), so a plain create_all() would silently leave those
    columns missing on every already-deployed database, and every
    is_verified check would then KeyError instead of working.

    This runs a one-time, idempotent ALTER TABLE for any column present in
    the Python Table definition but missing from the real database, then
    backfills existing rows: any account that existed BEFORE email
    verification was added is grandfathered in as already verified --
    locking out every pre-existing account the next time they log in,
    just because a feature was added after they signed up, would be a
    real, self-inflicted regression.
    """
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return  # brand new database -- create_all() already created this table with every column

    existing_cols = {c["name"] for c in inspector.get_columns("users")}
    new_cols = [c for c in users.columns if c.name not in existing_cols]
    if not new_cols:
        return

    bool_type = "BOOLEAN" if not IS_SQLITE else "INTEGER"
    with engine.begin() as conn:
        for col in new_cols:
            if col.name == "email_verified":
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col.name} {bool_type} DEFAULT 0"))
            else:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col.name} TEXT"))
        if any(c.name == "email_verified" for c in new_cols):
            # Grandfather in every account that existed before this column did.
            conn.execute(update(users).values(email_verified=True))


def init_db() -> None:
    """Create every table if it doesn't already exist, then apply any
    pending column migrations. Safe to call on every page load."""
    metadata.create_all(engine)
    _migrate_users_table()


def upsert_stmt(table: Table, index_elements: list):
    """
    Return the dialect-correct "INSERT ... ON CONFLICT DO UPDATE" statement
    builder for the current engine. Postgres and SQLite both support this
    upsert syntax but via different SQLAlchemy constructs -- this is
    exactly the kind of dialect difference this module exists to hide from
    every caller.
    """
    return pg_insert(table) if not IS_SQLITE else sqlite_insert(table)
