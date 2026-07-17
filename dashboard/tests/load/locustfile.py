"""
Unstructured Alpha — load / resilience test (Locust).

Targets the SEO FastAPI service (seo.unstructuredalpha.com) because it serves
real DB-backed, dynamically-rendered HTTP pages — the meaningful thing to load
test. (The Streamlit app renders over a websocket, so plain HTTP load only
exercises its initial shell + /_stcore/health; those are included as light
probes but are not the focus.)

WHAT IT EXERCISES
  - /ticker/{symbol}     DB read (latest score snapshot) + full HTML render
  - /signal/{signal_id}  DB read (signal snapshot) + HTML render
  - /signals/report      heavier aggregate page
  - /sitemap.xml         DB scan of all tickers/signals
  - /readyz /healthz     health probes (DB + Redis)
  - Streamlit / + /_stcore/health   shell + liveness

USAGE
  pip install locust
  # headless ramp, 50 users, spawn 5/s, 2 min, CSV output:
  locust -f tests/load/locustfile.py --headless \
         -u 50 -r 5 -t 2m \
         --host https://seo.unstructuredalpha.com \
         --csv results/ramp50 --only-summary

  # or the driver script:  python tests/load/run_ramp.py

The weights model a read-heavy public/crawler traffic mix. No writes, no auth,
no money movement — safe to run against production.
"""
from __future__ import annotations

import random

from locust import HttpUser, task, between

# Real IDs pulled from the live sitemap (2026-07-16). A representative sample —
# not the full 280/47, which would just thrash cache cold-misses unrealistically.
TICKERS = [
    "AAPL", "NVDA", "MSFT", "SPY", "QQQ", "TLT", "GLD", "XLE", "XLF", "HYG",
    "AMD", "META", "AVGO", "JPM", "XOM", "COP", "ABBV", "ADM", "ALB", "AES",
]
SIGNALS = [
    "consumer_sentiment", "bank_lending_standards", "copper", "copper_gold_ratio",
    "credit_card_delinquency", "crude_inventories", "construction_spending",
    "ata_trucking",
]

STREAMLIT_HOST = "https://app.unstructuredalpha.com"


class SeoVisitor(HttpUser):
    """A crawler / share-link visitor hitting the SEO service."""

    wait_time = between(0.5, 2.5)

    @task(10)
    def ticker_page(self):
        sym = random.choice(TICKERS)
        with self.client.get(f"/ticker/{sym}", name="/ticker/{symbol}",
                             catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"status {r.status_code}")

    @task(6)
    def signal_page(self):
        sig = random.choice(SIGNALS)
        with self.client.get(f"/signal/{sig}", name="/signal/{id}",
                             catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"status {r.status_code}")

    @task(2)
    def signals_report(self):
        self.client.get("/signals/report", name="/signals/report")

    @task(2)
    def sitemap(self):
        self.client.get("/sitemap.xml", name="/sitemap.xml")

    @task(1)
    def readyz(self):
        with self.client.get("/readyz", name="/readyz", catch_response=True) as r:
            # 503 here is a legitimate readiness signal, not a load failure.
            if r.status_code not in (200, 503):
                r.failure(f"status {r.status_code}")

    @task(1)
    def healthz(self):
        self.client.get("/healthz", name="/healthz")


class StreamlitVisitor(HttpUser):
    """Light probe of the Streamlit app shell (websocket render not covered)."""

    wait_time = between(1.0, 3.0)

    @task(3)
    def shell(self):
        self.client.get(f"{STREAMLIT_HOST}/", name="[st] /")

    @task(2)
    def health(self):
        self.client.get(f"{STREAMLIT_HOST}/_stcore/health", name="[st] /_stcore/health")
