# Reddit Marketing Posts — Unstructured Alpha
# Post these yourself. Do NOT post all on the same day — spread over 1–2 weeks.
# Most important: engage with every comment within the first hour of posting.

---

## POST 1 — r/algotrading (best audience, post this first)
**Karma requirement: usually 10+. Check your account has some activity first.**

**Title:**
I built an alternative data platform for equities: 38 signals (FRED, EIA, SEC EDGAR, FINRA), Bonferroni-corrected lag scans, out-of-sample validation. Here's what I found.

**Body:**
I spent the last several months building Unstructured Alpha — a signal intelligence dashboard that aggregates public alternative data into a per-ticker Confluence Score. Figured this crowd would appreciate the methodology details more than the pitch.

**What it actually does:**

38 signals across macro (yield curve, credit spreads, M2, jobless claims), energy (crude inventories, nat gas storage, rig count), insider transactions (Form 4 XML parsing from SEC EDGAR), short interest (FINRA semi-monthly data), 13F institutional positioning, congressional trades, options flow, and social sentiment.

Each signal is Z-score normalized over a 52-week rolling window, mapped to [0, 100] via `score = 50 + 30 * tanh(z/2)`, then directionally adjusted for signals that historically invert. The per-ticker Confluence Score is a correlation-weighted average of only the signals with statistically validated lead times for that specific ticker.

**The validation methodology (this is the part I care most about):**

For each signal × ticker pair, I run a lag scan across k = 1..16 weeks:
```
rho_k = corr(signal(t-k), return(t))
```
The best lag k* is only used if it:
1. Survives Bonferroni correction (alpha/16 ≈ 0.003 instead of 0.05)
2. Holds on a held-out OOS window (final 25% of the series, never touched during fitting)

Both conditions must be met. Without the correction, I was seeing ~30 spurious significant results per ticker just from multiple comparisons noise — that paper by Harvey, Liu & Zhu (2016) on factor zoo false discoveries is the direct motivation here.

**What survived:** Insider buying clusters, credit spread widening/tightening, crude inventory draws, jobless claims trends, and yield curve shape changes. Congressional trades are directionally correct but small sample. Short interest is noisy at the individual-security level.

**What didn't survive:** Most single-commodity signals, most sector ETF momentum proxies, and most of the social sentiment signals I tried (Google Trends + StockTwits). They pass in-sample, fail OOS — classic overfitting.

I publish these results openly on a Model Validation page rather than hiding the failures, because a platform where you can't see what doesn't work isn't actually useful.

**Tech stack if anyone's curious:** Python 3.12, Streamlit, Plotly, yfinance, pandas/scipy/SQLAlchemy, PostgreSQL on Render, Anthropic API for a weekly macro research note generator.

Live at: unstructuredalpha.com (no account needed to browse most of it)

Happy to get into any of the methodology details in comments.

---

## POST 2 — r/SideProject (post 3–4 days after Post 1)
**This subreddit is very welcoming to "I built this" posts. No restrictions.**

**Title:**
I built an alternative data intelligence platform for stocks — 28 pages, 38 signals, live on Render, free to try

**Body:**
Been building this on and off for about 6 months. It's called Unstructured Alpha.

The core idea: non-price data (insider trades, credit spreads, commodity inventory draws, congressional trade disclosures, institutional 13F shifts) tends to lead equity price moves by 2–8 weeks. Instead of watching price charts after the fact, the platform surfaces these signals before the market has fully priced them in.

**What it includes:**
- Signal Dashboard: 38 alternative data signals, each scored 0–100 with bullish/bearish/neutral status
- Ticker Deep Dive: full signal analysis for any equity, with a correlation-weighted Confluence Score, dual-axis price/signal chart, insider cluster detection, short interest history, and a "What would change my mind" block
- Factor Exposure: Fama-French style regression decomposing any ticker into market, size, value, momentum, and quality factor loadings
- Market Heatmap: S&P 500 sector treemap colored by signal-derived macro scores
- Signal Backtester: build custom signal combinations and backtest them
- Congress Tracker: live congressional trade disclosures from SEC EDGAR
- Export Report: download a PDF research report for any ticker
- Weekly Brief: AI-generated macro research note using Anthropic's Claude API

**Honest about limitations:** Most signals haven't been independently validated. The platform publishes OOS validation results for every signal including the ones that failed. The Confluence Score is directionally interesting but not a trading system.

**Stack:** Python 3.12 / Streamlit / Plotly / PostgreSQL / Render / fpdf2 / Anthropic API

Try it: unstructuredalpha.com — most pages are accessible without an account.

What would you add? Happy to take feedback.

---

## POST 3 — r/investing (post 5–7 days after Post 1)
**IMPORTANT: r/investing mods remove promotional posts fast. Lead with genuine value. Don't mention the platform name in the title.**

**Title:**
I analyzed 38 alternative data signals for predictive content in equity returns. Here's what actually worked (OOS) and what didn't.

**Body:**
I've spent the last several months systematically testing whether public alternative data series have statistically reliable lead times over equity returns. Posting the findings because I think the methodology is useful regardless of whether you use my specific platform.

**The signals I tested** (all from public sources — FRED, EIA, SEC EDGAR, FINRA):
- Macro: yield curve slope, HY credit spreads, jobless claims, M2 money supply, retail sales, consumer sentiment, housing starts, durable goods orders, industrial production
- Energy: crude oil inventories (EIA), natural gas storage, rig count
- Credit/liquidity: investment grade spreads, TED spread, financial conditions indices
- Event-driven: insider Form 4 transactions, FINRA short interest, institutional 13F positioning shifts, congressional trade disclosures

**The methodology:** For each signal × equity pair, I scan lags 1–16 weeks, take the best Pearson r, apply Bonferroni correction (alpha/16), and require the signal to hold on a held-out OOS window (final 25% of the series).

**What survived OOS:**
- Insider buying clusters (2+ insiders buying within 21 days) — strongest signal, but small N for most tickers
- HY credit spread widening: reliable leading indicator of risk-off equity drawdowns, ~4–6 week lead
- Crude inventory draws: leads energy sector by ~3–5 weeks
- Yield curve slope: well-established in the literature, confirmed here at the sector level
- Jobless claims 4-week moving average: leads cyclical equities

**What didn't survive:**
- Most single-commodity proxies (gasoline, lumber, copper): pass in-sample, fail OOS reliably
- Social sentiment (search trends, forum activity): very noisy, highly regime-dependent
- Short interest alone: useful context but not a reliable standalone predictor
- Most macro signals for individual equities: the signal is real at the sector/index level but attenuates badly for single stocks

The key methodological failure mode is multiple comparisons without correction. If you test 16 lags without Bonferroni, you'll find "significant" predictors for almost any series — they just won't hold up OOS.

Happy to discuss the methodology in comments. I built a platform around this if anyone's curious (unstructuredalpha.com) but the findings stand on their own.

---

## POST 4 — r/stocks (post 8–10 days after Post 1)
**Lighter/more accessible tone. r/stocks has moderate spam filter.**

**Title:**
I've been tracking insider trades, credit spreads, energy inventories, and 35 other alternative data signals for months. Here's a quick summary of what they're saying right now.

**Body:**
I built a dashboard that aggregates 38 public data signals across macro, energy, credit, and event-driven categories. Wanted to share a snapshot of where things stand, because I find this kind of cross-signal view more useful than any single indicator.

**What alternative data is currently showing** (as of posting date — these update daily):

Most of the macro signals I track have [FILL IN CURRENT SIGNAL STATE FROM YOUR DASHBOARD BEFORE POSTING — e.g., "the HY credit spread signal is mildly bearish, having widened ~85bps over the past 6 weeks. The yield curve has steepened modestly but remains inverted at the 2Y/10Y spread. Crude inventories drew down sharply last week, which has historically been bullish for energy names with a 3–5 week lag."]

The Confluence Score across all 38 signals is currently [FILL IN SCORE]/100, which puts the macro backdrop in [bullish/neutral/bearish] territory.

I track all of this at unstructuredalpha.com — most of it is free to browse without an account.

Questions about any specific signal happy to discuss.

---

## NOTES ON POSTING STRATEGY

**Timing:** Post between 8–10am ET on weekdays. Avoid Mondays and Fridays.

**Engage fast:** Reply to every comment within 1 hour of posting. Reddit's algorithm heavily weights early comment velocity. A post with 20 upvotes and 15 comments will get 10x the distribution of a post with 20 upvotes and 2 comments.

**For Post 4 specifically:** Fill in the [FILL IN] sections with actual current signal readings from your dashboard before posting. A post about live data that shows actual numbers is dramatically more credible than one that's vague.

**Don't post all four at once.** Spread them over 2 weeks minimum. Posting from the same account to multiple finance subreddits within the same week triggers Reddit's spam filter.

**If a post gets traction (50+ upvotes):** Follow up in the comments with screenshots, deeper methodology details, or a specific example of a signal call that played out. This is where you convert readers to users.

**Cross-post r/algotrading post to r/quant** after it gets some upvotes — that's allowed and extends reach.
