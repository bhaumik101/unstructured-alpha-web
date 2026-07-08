# Social Media Batch 2 — Unstructured Alpha
# July 2026 — Post these spread 2–3 days apart

---

## TWITTER / X POSTS

### Thread 1 — Signal Education (best for engagement)
**Post as a thread, 4 tweets:**

**Tweet 1 (hook):**
> Most traders watch price to predict price.
>
> The signals that actually predicted market moves 4–8 weeks ahead: insider Form 4 clusters, HY credit spreads, EIA crude draws, yield curve slope.
>
> Here's why each one works — and why most "alternative data" doesn't: 🧵

**Tweet 2:**
> Insider Form 4 clusters are the strongest signal I've found.
>
> Not a single insider buying. *Two or more insiders from the same company buying within 21 days of each other.*
>
> That's when it becomes statistically meaningful. It's rare, which is also what makes it signal vs. noise.

**Tweet 3:**
> HY credit spreads widening → equities weaken 4–6 weeks later.
>
> It makes sense: when borrowing costs spike for junk issuers, leverage unwinds. Equity weakness follows.
>
> ICE BofA OAS is free on FRED (BAMLH0A0HYM2). One of the most reliable macro leads I've found.

**Tweet 4 (CTA):**
> I track all of this — 47 signals total — at unstructuredalpha.com
>
> Model Validation page shows exactly which signals have statistically significant lead times (with OOS testing), and which ones failed.
>
> Most pages are free to browse.

---

### Tweet 2 — Transparency angle (low-effort, high trust)
> Hot take: most "quant" fintech products bury their failures.
>
> I publish mine. The signals that didn't make the cut — social sentiment, single-commodity plays, short interest alone — are all on a public Model Validation page.
>
> If a platform only shows you what worked, it's a marketing deck, not a tool.
>
> unstructuredalpha.com/Model_Validation

---

### Tweet 3 — Live data snapshot (update numbers before posting)
> What the data shows right now (July 6, 2026):
>
> 📊 47 signals tracked
> 🟢 13 BULLISH
> 🔴 8 BEARISH
> ⚪ 26 NEUTRAL
>
> Macro regime: MIXED SIGNALS
>
> VIX Term Structure just flipped bullish. US Crude Inventories also flipped bullish this week.
>
> See the full picture: unstructuredalpha.com/Today_Digest

---

### Tweet 4 — Short Squeeze radar highlight
> My Short Squeeze Radar just flagged 0 HIGH CONVICTION setups today, but here's the broader radar:
>
> BTC-USD: squeeze score 50
> SAIA: 44
> WMT: 46
> CNI: 44
>
> (Score = short interest + macro alignment + insider cluster signal, 0–100)
>
> Full methodology + live list: unstructuredalpha.com/Short_Squeeze_Radar

---

### Tweet 5 — Product feature highlight
> Most dashboards show you signals. I show you which ones actually predicted returns.
>
> The Deep Correlation Scan runs lag analysis (1–16 weeks) on any ticker × signal pair with Bonferroni correction and a held-out OOS test window.
>
> It's not "correlated." It's "survived the test you would've used if you were rigorous."
>
> Free at unstructuredalpha.com

---

### Tweet 6 — Hook/question format
> Question for my finance Twitter:
>
> If you could only watch ONE non-price data series to anticipate S&P 500 drawdowns, what would you pick?
>
> Mine: HY credit spreads (FRED: BAMLH0A0HYM2)
>
> Historically leads equity weakness by 4–6 weeks and it's publicly available. What are you watching?

---

### Tweet 7 — Myth-bust format
> "Short interest is a great contrarian indicator"
>
> Tested this across 40+ tickers. Short interest alone: not a reliable predictor of forward returns in OOS testing.
>
> Short interest + macro regime + insider cluster signal? That's different. The combination is what the Short Squeeze Radar tracks.
>
> Context matters.

---

### Tweet 8 — Builder story
> 6 months of evenings → 28+ pages of alternative data intelligence
>
> What I didn't expect: the hardest part wasn't the data engineering.
>
> It was figuring out which correlations were spurious vs. genuinely predictive.
>
> And then being honest enough to publish the failures openly.
>
> unstructuredalpha.com — 7-day free Pro trial

---

### Tweet 9 — Weekly brief hook
> Every week I publish an AI-generated macro research note on unstructuredalpha.com/Weekly_Brief
>
> It's generated from live signal state — not from generic market commentary.
>
> Last week's brief flagged: VIX term structure inversion (bearish), oil inventory draws continuing (bullish for energy), yield curve normalization (macro tailwind).
>
> Worth a read.

---

### Tweet 10 — "Did you know" format
> Did you know the yield curve has been positively sloped again since mid-2025?
>
> 10Y at 4.38%, 2Y at 4.07% — spread +31bps
>
> After 2+ years of inversion (2022–2024), a re-steepening is historically a late-cycle signal.
>
> What it means for equities: historically bullish 6–12 months out, but watch for credit spread widening first.

---

---

## REDDIT POSTS

---

### POST 5 — r/quant
**Post after r/algotrading gets traction. Build karma first.**
**Flair: Research**

**Title:**
Bonferroni vs. BH correction in lag-scan analysis — practical tradeoffs at ~40 signals × 80 tickers

**Body:**
I've been running a lag scan on public alternative data signals (FRED, EIA, SEC EDGAR, FINRA) for equity return prediction and want to get this sub's take on the correction approach.

**Setup:** For each signal × equity pair, scan lags 1–16 weeks, test Spearman correlation with Bonferroni correction (alpha/16 ≈ 0.003). Only keep a signal if it also holds on a held-out OOS window (final 25% of data).

**The practical problem:** Bonferroni is very conservative. At 40+ signals × 80+ tickers × 16 lags = ~51,200 tests, I'm probably throwing away real effects along with noise. But every time I relaxed to BH correction, I started finding things that looked real in-sample and fell apart immediately in OOS testing.

**What I've tried:**
- Bonferroni per ticker (not global): conservative but manageable
- BH at q=0.05 across all tests: too permissive, OOS failure rate spiked
- BH at q=0.01 with minimum 3 years of data per signal: somewhere in between

The things that survived even Bonferroni: insider buying clusters, HY credit spread widening, EIA crude inventory draws, yield curve slope. The things that only "survived" under relaxed BH: every social sentiment variant I tried.

Is anyone using hierarchical multiple testing procedures here? Or blocking by signal category (macro/event-driven/credit) and correcting within blocks?

The platform this powers is at unstructuredalpha.com if you want to see the OOS results — the Model Validation page shows which signals passed and which didn't.

---

### POST 6 — r/stocks
**New data post — replace bracketed values with live data before posting**
**Best timing: Monday or Tuesday morning ET**

**Title:**
Here's what 47 alternative data signals are saying about the market right now (July 2026)

**Body:**
I've been running a dashboard that tracks 47 macro and event-driven signals — credit spreads, EIA inventories, insider Form 4 activity, yield curve, congressional trades, options sentiment, and more. Sharing a live snapshot.

**This week's picture (July 6, 2026):**

*Macro regime:* MIXED SIGNALS — 13 bullish / 8 bearish / 26 neutral across 47 signals.

*What just flipped bullish:* VIX Term Structure turned bullish this week (short-dated vol falling relative to longer-dated = market calming). US Crude Inventories also flipped bullish.

*What's worth watching:*
- Yield curve is positive (+31bps, 10Y/2Y) for the first time since 2022. Historically a late-cycle macro tailwind.
- HY credit spreads remain near multi-year lows. No credit stress signal yet.
- Insider buying clusters are sparse. The insider data right now leans cautious on tech/semis specifically.

*"About to Flip" signals (within 5pts of threshold):*
The dashboard shows a few signals approaching their bull/bear thresholds. These are worth watching but not actionable yet.

---

This data comes from unstructuredalpha.com. Most pages are free without an account — the Signal Dashboard, Today's Brief, and Ticker Deep Dive don't require signup. The Short Squeeze Radar and Congress Tracker are also free.

Happy to pull the signal data for any specific ticker if people are curious.

---

### POST 7 — r/personalfinance
**Angle: accessible, practical, non-technical. No jargon.**

**Title:**
I built a free tool that tracks 47 economic data points and tells you the market's current "mood." Here's how I use it.

**Body:**
I know this sub is usually about budgets and index funds (rightfully so), but I think this is relevant for people who want to understand what's happening in markets before they decide to add to their portfolio or hold off.

I built unstructuredalpha.com — a dashboard that tracks 47 public economic and market signals in one place. Things like:
- What the yield curve is doing (the recession indicator most people have heard of)
- Whether credit markets are showing stress (HY credit spreads — this usually leads equity weakness by weeks)
- What company insiders are doing with their own stock
- Whether energy inventories are building or drawing (leads oil stock moves)
- What's happening with unemployment claims week over week

None of this is "buy this stock now" advice. It's a macro picture. The main thing I use it for personally:

**When the "macro regime" shifts to bearish**, I get more cautious about lump-sum additions and lean toward dollar-cost averaging instead.

**When multiple signals line up bullish** (yield curve positive, credit spreads tight, insider clusters appearing), I treat that as a green light for scheduled contributions.

Right now the dashboard reads MIXED SIGNALS — 13 bullish / 8 bearish / 26 neutral. Neither full-speed-ahead nor red-flag territory.

Most pages are completely free. You don't need an account to browse the Signal Dashboard, Today's Brief, or Ticker Deep Dive.

unstructuredalpha.com

Happy to answer questions about what any of the signals actually measure.

---

### POST 8 — r/dataisbeautiful
**Angle: the visualization. Include screenshots when posting — use the 5 PH screenshots.**

**Title:**
I mapped 47 macro signals (credit spreads, EIA data, insider trades, yield curve) into a daily bull/bear intelligence dashboard [OC]

**Body:**
[OC] I've been building this for about 6 months — Unstructured Alpha is a daily macro signal intelligence platform that pulls 47 public data signals and visualizes them as a coordinated picture.

The data comes from: FRED (Federal Reserve economic data), EIA (energy inventories), SEC EDGAR (insider Form 4 transactions), FINRA (short interest), CBOE (options sentiment), and a few other public sources.

**What's visualized:**

*Signal Dashboard* — each signal displayed as a card with its current bull/bear/neutral state, score (0–100), trend direction, and days since last flip. Organized by macro category.

*Ticker Deep Dive* — for any ticker, shows a radar chart of which signal categories (macro, energy, credit, event-driven) are bullish vs. bearish for that specific stock. Plus an AI-generated explanation of why the score is what it is.

*Market Heatmap* — S&P 500 sector treemap colored by Confluence Score. Immediate visual of which sectors macro data favors.

*Short Squeeze Radar* — combines short interest + macro signal state + insider cluster detection into a single squeeze probability score.

Stack: Python / Streamlit / Plotly / PostgreSQL / Render

Live at unstructuredalpha.com — most pages are free without an account.

Happy to answer questions about the visualization choices or the underlying signal methodology.

---

## POSTING SCHEDULE

| Post | Subreddit | Timing |
|------|-----------|--------|
| Post 5 | r/quant | After r/algotrading gets traction |
| Post 6 | r/stocks | Monday/Tuesday 8–10am ET, July 7–8 |
| Post 7 | r/personalfinance | 5+ days after Post 6 |
| Post 8 | r/dataisbeautiful | Anytime, needs screenshots attached |

**Twitter threads:** Space 2 days apart. Thread 1 first (highest engagement potential), then single tweets in order.

## NOTES

- **r/stocks Post 6:** Pull live Today's Brief data before posting. Check unstructuredalpha.com/Today_Digest for the actual signal counts.
- **r/dataisbeautiful:** This post REQUIRES attaching the 5 screenshots as images. Without visuals it will not perform in that sub.
- **Twitter Thread 1:** Best time to post: 8–10am ET weekdays. Quote-tweet it yourself with a follow-up data point 24h later to extend lifespan.
- **Reply velocity:** For Reddit, reply to every comment in the first hour. For Twitter, retweet and reply to anyone who engages.
