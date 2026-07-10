#!/usr/bin/env python3
"""
dashboard/seo_entry.py  —  Render start-command entry point for the SEO service.

Why this exists instead of `python -m uvicorn seo.main:app`:
  Render's rootDir setting changes the *build* CWD (pip install), but the
  process runner does not reliably set that same CWD for the started process.
  As a result, `python -m uvicorn seo.main:app` fails because sys.path does
  not contain the parent of seo/ (dashboard/).

  This script uses __file__ — which always resolves to its own absolute path
  regardless of the CWD at invocation — to unconditionally add dashboard/ to
  sys.path before uvicorn imports anything. No chicken-and-egg.

Render start command:  python seo_entry.py
"""
import os
import sys

# Resolve to dashboard/ — the directory that contains seo/, utils/, etc.
# Works regardless of whether Render's CWD is repo-root or dashboard/.
_dashboard = os.path.dirname(os.path.abspath(__file__))
if _dashboard not in sys.path:
    sys.path.insert(0, _dashboard)

import uvicorn  # noqa: E402 — must come after sys.path is set

if __name__ == "__main__":
    uvicorn.run(
        "seo.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8502)),
        reload=False,
    )
