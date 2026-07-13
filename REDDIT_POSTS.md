# Reddit Posts — Unstructured Alpha (Updated 2026-07-12)
# STRATEGY: Post one at a time, spread 1–2 days apart.
# Respond to every comment within 2 hours. Stay educational — no Pro pitching in comments.
# Build karma in each sub by commenting on 3–5 posts BEFORE you post.

---

# NEW BATCH (Post this week)

## Post A — r/algotrading
**Title:** I built a 38-signal macro scoring system with full out-of-sample validation published — what I learned about which signals actually hold up

**Body:**

Been at this for about 8 months. 38 independent macro and alternative data signals scored daily on a 0–100 percentile scale: HY credit spreads, FINRA short interest, SEC Form 4 insider clusters, CBOE put/call, EIA energy inventories, copper/gold ratio, TIPS breakeven, VIX term structure, ISM PMI, yield curve slope, and more.

Platform: unstructuredalpha.com

What survived Bonferroni-corrected lag scans against 12-week forward returns:
- HY credit spreads: consistent 4–8 week lead on broad market direction
- Insider buy clusters (SEC Form 4): strong for individual names when 2+ officers buy within 21 days
- Yield curve slope: good for sector rotation, not individual stock prediction
- CBOE put/call ratio: best as contrarian indicator at extremes

What did not:
- Short interest alone: too noisy without a catalyst
- 13F institutional positioning: 90-day reporting lag kills timeliness
- Social sentiment (Google Trends): high variance, easily contaminated by news cycles

Bonferroni killed ~30% of initially significant lag relationships. The Model Validation page publishes all of this including the failures — which is not something you see on most financial platforms.

Curious if anyone has done similar lag analysis and whether you found Bonferroni too conservative for macro signal work.

---

## Post B — r/investing
**Title:** I got tired of quant scores with no methodology, so I built a free macro signal dashboard that shows exactly what drives the score

**Body:**

TipRanks Smart Score, Seeking Alpha Quant Rating — composite scores with zero visibility into how they are computed or how they have actually performed.

Spent 8 months building what I wanted: 38 macro and alternative data signals scored daily from FRED, SEC EDGAR, FINRA, EIA, CBOE. Every signal explained. Out-of-sample validation published on the Model Validation page — including the ones that failed.

Signal Dashboard is free. Ticker Deep Dive is free. Model Validation is free.

When a signal does not hold up out-of-sample, the platform labels it clearly. A score you cannot interrogate is not a signal, it is a number with a gradient background.

Not buy/sell recommendations. Macro context for your own research.

unstructuredalpha.com — happy to answer methodology questions.

---

## Post C — r/stocks
**Title:** How I think about macro backdrop before sizing into a position — systematized it, here is what it is showing this week

**Body:**

The gap between "credit spreads are widening" and "what does that mean for my NVDA position" has always frustrated me. Built something to bridge it.

For any ticker: lag scan finds which macro signals historically correlate with that sector's forward returns. Weight by correlation strength and significance. Score 0–100. Above 65 = multiple bullish signals aligned. Below 35 = headwinds stacked.

What it is showing this week:
- AI Infrastructure: Elevated (copper/gold bullish, insider activity positive, credit spreads tight)
- Energy: Neutral to Bullish transition (EIA draws supportive, watching rig count)
- Homebuilders: Mixed (Michigan Sentiment at 67 is a watch level)
- Nuclear/Utilities: Still bullish (grid buildout thesis supported)

Validation published for every signal including failures. Not investment advice.

Free: unstructuredalpha.com

---

## Post D — r/SecurityAnalysis
**Title:** Systematic macro framework to complement fundamental analysis — full methodology and validation published

**Body:**

Built something meant to complement fundamental work: a systematic read on whether macro backdrop supports a sector thesis.

Premise: strong fundamentals do not guarantee returns if the macro environment is hostile to the sector. Most valuation models treat macro as sentiment, not as a systematic input.

Signals from public primary sources only:
- FRED: yield curve, HY/IG credit spreads, TIPS breakeven, ISM PMI, Michigan sentiment
- SEC EDGAR: Form 4 insider transactions (direct XML parsing, not third-party aggregates)
- FINRA: biweekly short interest normalized by float
- EIA: weekly crude/gas storage, rig count
- CBOE: put/call ratio, VIX term structure (VIX9D vs VIX30)
- Congressional disclosures (45-day lag acknowledged and labeled)

Validation: lag scans vs 4–12 week forward returns on 150+ tickers. Bonferroni corrected. Second-half holdout. Failures labeled on Model Validation page — not buried.

Can do: tell you whether macro backdrop is structurally supportive of a sector thesis.
Cannot do: replace fundamental research or tell you whether a company is cheap.

Platform: unstructuredalpha.com

---

## Timing

- r/algotrading: Monday morning
- r/investing: Wednesday afternoon
- r/stocks: Thursday morning
- r/SecurityAnalysis: Friday morning

---


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
**Status: READY TO POST (data filled in as of June 30, 2026)**
**⚠️ Before posting: pull the live Confluence Score from unstructuredalpha.com → Today's Brief and replace [CONFLUENCE SCORE] below.**

**Title:**
Been tracking insider trades, credit spreads, crude inventories, and 35 other data signals for months. Here's what they're saying right now.

**Body:**
I run a dashboard that pulls 38 public alternative data signals and aggregates them into a daily picture of where macro, credit, and event-driven data are pointing. Cross-signal views are more useful than any single indicator, so sharing a live snapshot.

**What the data looks like right now (week of June 30, 2026):**

*Credit/macro:* HY credit spreads (ICE BofA OAS) widened ~15 bps during June to 2.78% — still near multi-year lows but the direction flipped from tightening to widening mid-month, which is worth watching. Yield curve is now positively sloped for the first time since 2022 (10Y at 4.38%, 2Y at 4.07%, spread +31 bps). Jobless claims fell to 215K the week of June 20 after three weeks in the 226-229K range — labor market not cracking yet. 4-week MA sits at ~223K.

*Energy:* EIA crude inventories have drawn down for 7 consecutive weeks. The last three draws: -7.2M (June 5), -8.3M (June 12), -6.1M (June 19) — all well above consensus. Cushing hub is sitting near its lowest level since 2014. Historically the EIA draw streak leads energy equity outperformance by 3–5 weeks in my lag-scan data. XOM, CVX, SLB are the names that correlate most strongly with this signal.

*Insider activity:* Buying clusters are sparse right now. The standout this week is the opposite — 61 sell clusters vs. 28 buy clusters on June 26, with 61% of insider-sell dollars concentrated in chips and AI hardware (Nvidia, Applied Materials, Marvell, Credo, Dell). When company insiders are selling in concert at this scale it's the signal I track most closely, and it's pointing cautious on semis specifically.

*Overall Confluence Score:* [CONFLUENCE SCORE]/100 across all 38 signals — pull this from the dashboard before posting. Based on the above the macro backdrop looks neutral-to-slightly-bullish overall (yield curve normalizing + labor resilience + crude draws), but the insider selling in AI/semis skews it bearish for that specific sector.

---

I track all of this at unstructuredalpha.com, most of it is free to browse. The Insider page and Deep Correlation Scan don't require an account.

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
