# Show HN Draft

**Title (60 chars):**
Show HN: I built a stock signal platform using alternative data (28 signals)

---

**Post body:**

I spent the last 6 months building Unstructured Alpha (https://unstructuredalpha.com) — a dashboard that scores 28 macro and alternative data signals daily and synthesizes them into a bull/bear/neutral market pulse.

The honest version: most of what I tried didn't work. I started by scraping Reddit and Twitter sentiment — garbage signal, couldn't distinguish genuine conviction from noise. Tried using options flow as a leading indicator for earnings — looked great in backtesting, fell apart live during volatile periods. The signals that actually survived were the boring ones: credit spreads widening before equity drawdowns, energy inventories correlating with sector rotation, the yield curve doing what the yield curve does.

What it does:
- Scores 28 signals (credit, yields, energy, Fed liquidity, insider activity, short interest, options sentiment) on a 0–100 scale daily
- Detects when signals "flip" bull→bear or vice versa
- Sector-relative percentile ranking — is XOM's credit spread spread tight or wide relative to energy sector history?
- Signal→price overlay charts showing lag relationships with statistical validation
- Morning digest email with flips and movers
- 7-day free trial, $20/mo after

Stack: Streamlit + PostgreSQL + Render + FRED/EIA/CBOE/SEC EDGAR APIs + Resend for email. No LLM smoke and mirrors in the signal scoring — everything is rule-based off real data series.

The hardest part wasn't the data engineering, it was figuring out which correlations were spurious vs. genuinely predictive. I did lag-scan analysis with Bonferroni correction on each signal and published a Model Validation page showing which signals have statistically significant lead times. Some don't, and I say so explicitly.

Happy to answer questions about methodology or specific signal construction.

---

**Notes:**
- Post Tuesday–Thursday 8–10am ET for best visibility
- Reply fast to early comments — HN rewards discussion
- Don't pitch in comments, answer technical questions
- If it gets traction, cross-post to r/quant
