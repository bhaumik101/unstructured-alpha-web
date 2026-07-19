"""Run the scoring cron locally against production, without Render's 512MB cap.

Why this exists: `. ./.env.render` cannot be sourced by bash. Line 10 is

    RESEND_FROM_EMAIL=Unstructured Alpha <noreply@unstructuredalpha.com>

which is unquoted and contains spaces and a `<`, so bash aborts on a syntax
error. In a `set -a && . ./.env.render && python ...` chain that abort silently
prevents the command from running at all — which is exactly how a backfill
appeared to run for ten minutes while writing nothing. python-dotenv parses the
file correctly, so the env is loaded in-process instead.

Everything after `--` is forwarded to cron.score_universe:

    python scripts/run_scorer.py -- --tier core --budget 400
    python scripts/run_scorer.py -- --tier rest --budget 3000
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

DASHBOARD = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DASHBOARD))

from dotenv import load_dotenv  # noqa: E402

env_file = DASHBOARD / ".env.render"
if not env_file.exists():
    sys.exit(f"missing {env_file}")
load_dotenv(env_file)

db = os.environ.get("DATABASE_URL", "")
if not db:
    sys.exit("DATABASE_URL not loaded — refusing to run against a fallback DB")
if db.startswith("sqlite"):
    # utils.db silently falls back to local SQLite when DATABASE_URL is absent,
    # so a run that looks successful can write to an empty local file instead of
    # production. Fail loudly rather than produce a convincing no-op.
    sys.exit("DATABASE_URL points at SQLite — this would not touch production")

# The local machine has no 512MB ceiling; the guard exists for Render.
os.environ.setdefault("SCORE_MAX_RSS_MB", "12000")

host = db.split("@")[-1].split("/")[0] if "@" in db else "?"
print(f"[run_scorer] target host: {host}", flush=True)

argv = sys.argv[1:]
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
sys.argv = ["score_universe", *argv]

from cron.score_universe import main  # noqa: E402

main()
