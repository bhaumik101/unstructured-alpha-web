# Reddit Posts — Unstructured Alpha
# STRATEGY: Post one at a time, spread 5–7 days apart.
# Build karma in each sub by commenting on 3–5 posts BEFORE you post.
# Reply to every comment within the first hour — this is what drives distribution.

---

## POST 1 — r/algotrading
**Status: First attempt removed (new account). Comment on a few posts there first, then repost.**
**Flair: Data**

**Title:**
I kept getting burned by in-sample backtests, so I built a validation framework across 38 alternative data signals. Here's what actually held up OOS.

**Body:**
Honest question for this sub: how many of you have had a signal look incredible in backtesting, then completely fall apart when you actually trade it?

I burned myself enough times that I stopped trusting in-sample results entirely and built something to validate properly. The result is Unstructured Alpha — I've been running it for several months across 38 public data signals. Here's what I found.

**The setup:**

For each signal × ticker pair, I scan lags 1–16 weeks and only keep a signal if it:

1. Survives Bonferroni correction (alpha/16 ≈ 0.003, not 0.05)
2. Holds on a fully held-out OOS window (final 25% of data, never touched during fitting)

Both. Not one or the other.

Without the correction I was finding ~30 "significant" predictors per ticker that were pure noise. Harvey, Liu & Zhu (2016) covers exactly this failure mode.

**What survived:**

- Insider buying clusters (2+ insiders within 21 days) — strongest signal, but N is small per name
- HY credit spread widening — reliable 4–6wk lead on risk-off drawdowns
- EIA crude inventory draws — leads energy names ~3–5 weeks
- Jobless claims 4wk MA — leads cyclicals at the sector level
- Yield curve slope — real, but mostly at index level, not individual stocks

**What didn't:**

- Single-commodity signals (gasoline, copper, lumber) — textbook overfitting
- Social sentiment (Google Trends, StockTwits) — noise, regime-dependent, basically useless standalone
- Short interest alone — useful context but not predictive on its own

All failures are published openly on a Model Validation page. If you can't see what didn't work, the platform isn't useful.

Try it at unstructuredalpha.com — most pages are free without an account. There's a Deep Correlation Scan where you can run the lag analysis yourself on any ticker/signal pair and see the OOS split.

Happy to get into the methodology. Curious if anyone's made BH correction work better than Bonferroni at this scale.

---

## POST 2 — r/SideProject
**Post 5–7 days after the first successful post. No karma requirements.**

**Title:**
6 months of evenings later — I built a 28-page alternative data intelligence platform for stocks. Here's what I learned.

**Body:**
Unstructured Alpha has been my obsession for the last 6 months.

The idea started simple: non-price data moves *before* prices, not after. Insider transactions, credit spreads, energy inventory draws, congressional trades — these have historically led equity price moves by 2–8 weeks. So instead of watching charts after something's already happened, the platform tries to surface what the data is saying *right now*.

**What it does:**

38 signals across macro, energy, credit, and event-driven categories. Everything is validated with proper out-of-sample testing (I'll explain below). The Confluence Score per ticker is a correlation-weighted composite of only the signals that actually passed validation for that specific name.

Pages: Signal Dashboard, Ticker Deep Dive, Factor Exposure, Market Heatmap, Signal Backtester, Congress Trade Tracker, Options Flow, Export Report, and a weekly AI-generated macro brief.

**The thing I'm most proud of:**

The validation is honest. I publish OOS results for every signal including the ones that failed — social sentiment didn't make it, most commodity signals didn't, short interest alone isn't reliable. Hiding failures is how you end up with a useless product.

**Stack:** Python 3.12 / Streamlit / Plotly / PostgreSQL on Render / Anthropic API

Live at unstructuredalpha.com — most pages work without signing up.

What would you change? Genuinely open to feedback.

---

## POST 3 — r/investing
**Post 5–7 days after Post 2. Do NOT mention the platform name in the title — mods remove it fast.**

**Title:**
I tested 38 public alternative data signals for predictive power in stock returns. Here's what actually worked (and what flopped).

**Body:**
Spent the last several months systematically testing whether public data has reliable lead times over equity returns. Sharing the methodology here because I think it holds up regardless of whether you use my specific tool.

**What I tested** (all free/public — FRED, EIA, SEC EDGAR, FINRA):

Macro: yield curve slope, HY credit spreads, jobless claims, M2, retail sales, industrial production
Energy: EIA crude inventories, nat gas storage, rig count
Event-driven: insider Form 4 transactions, FINRA short interest, 13F positioning shifts, congressional trades

**How I validated:**

Lag scan 1–16 weeks per signal × equity pair. A signal only "counts" if it survives Bonferroni correction AND holds on a held-out OOS window (final 25%, never touched during fitting). Without the correction I was finding false positives constantly — testing 16 lags without adjusting the threshold is how you fool yourself.

**What actually worked OOS:**

Insider buying clusters are the strongest signal when they appear. HY credit spread widening reliably leads risk-off moves 4–6 weeks out. EIA crude draws lead energy names ~3–5 weeks. Yield curve slope is real but mainly at the sector level, not individual stocks.

**What flopped:**

Social sentiment failed almost universally. Single commodity signals (gasoline, copper, lumber) look great in-sample and fall apart OOS every single time. Short interest alone is not a reliable predictor.

I built a platform around this if anyone wants to explore it: unstructuredalpha.com. But the findings are what matters here — happy to go deep on any of them in comments.

---

## POST 4 — r/stocks
**Post 5–7 days after Post 3. Fill in [CURRENT DATA] sections from your dashboard before posting.**

**Title:**
Been tracking insider trades, credit spreads, crude inventories, and 35 other data signals for months. Here's what they're saying right now.

**Body:**
I run a dashboard that pulls 38 public alternative data signals and aggregates them into a daily picture of where macro, credit, and event-driven data are pointing. Cross-signal views are more useful than any single indicator, so sharing a live snapshot.

**What the data looks like right now:**

[FILL IN before posting — pull from Signal Dashboard + Today's Brief. Example:]

*Credit/macro:* HY credit spreads are [tightening/widening — X bps over Y weeks]. Yield curve [shape]. Jobless claims [trend].

*Energy:* EIA crude inventories [drew down/built] last week. Historically this [leads/lags] energy sector by ~3–5 weeks.

*Insider activity:* [Any notable clusters this week from your insider page]

*Overall Confluence Score:* [X]/100 across all 38 signals — putting the macro backdrop in [bullish/neutral/bearish] territory.

---

I track all of this at unstructuredalpha.com, most of it is free to browse.

Happy to pull numbers on any specific signal or sector if people are curious.

---

## POSTING NOTES

**Why r/algotrading removed the first attempt:**
New account = instant mod suspicion. Spend a week commenting genuinely on threads in that sub, then repost. The content is good — the account trust score is the issue.

**Timing:** 8–10am ET, Tuesday–Thursday. Avoid Mondays and Fridays.

**Reply fast:** Comment velocity in the first hour is what Reddit's algorithm weights most. Reply to everyone.

**When a post gets 50+ upvotes:**
Follow up with a concrete example — a signal that called something that played out, with dates and numbers. This is what converts readers to signups.

**Cross-posting:**
After r/algotrading gets traction, cross-post to r/quant. Allowed, expands reach.
