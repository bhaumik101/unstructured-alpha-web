# Reddit Post Drafts — Unstructured Alpha

Posting guidelines for all subreddits:
- Disclose you built it (flair as "I built this" or mention "I built" in title where allowed)
- No misleading claims — all wording is defensible from the platform's actual methodology
- NOT financial advice disclosure in body of every post
- Never use words like "guaranteed", "never lose", "100% accuracy"
- Be genuinely helpful — answer follow-up questions openly

---

## POST 1 — r/algotrading
**Flair:** Discussion / Project

**Title:**
I built a dashboard that aggregates 38 alternative data signals (FRED, SEC EDGAR, FINRA, EIA) into a per-ticker Confluence Score — methodology fully published, including where it fails

**Body:**
Background: I got frustrated that most retail-facing quant platforms (TipRanks Smart Score, SA Quant) treat their scoring methodology as a trade secret. If you can't inspect the formula, you can't evaluate whether the score is actually predictive or just marketing.

So I built my own. Unstructured Alpha aggregates 38 signals across:
- Macro: 10-year yield, HY credit spreads, M2, TIPS breakeven, dollar index, copper/gold ratio
- Energy: crude inventories (EIA), nat-gas storage, rig count
- Institutional: 13F positioning changes, insider Form 4 transactions, congressional trades
- Short interest (FINRA biweekly filings)
- Sentiment: VIX term structure, put/call ratio, FedSpeak hawkishness (AI-scored FOMC text), Michigan consumer sentiment
- Earnings: transcript sentiment (Claude Haiku), ISM PMI, options unusual activity

Each signal goes through:
1. 52-week rolling z-score normalization
2. tanh(z/2) * 30 + 50 mapping to [0, 100]
3. Walk-forward lag scan (k = 1..16 weeks), Bonferroni corrected (alpha/m = 0.05/16)
4. OOS held-out validation window (final 25% of data)
5. Lag decay monitoring every 30 days

Signals that don't survive the validation are excluded and noted on a public Model Validation page — including which ones failed and why. This is deliberately the opposite of how commercial platforms handle their failures.

The Confluence Score for a ticker is the equal-weighted average of its validated signals, with insider/13F/short-interest capped at 12% each since they're security-specific rather than macro regime data.

What it does NOT claim:
- This is not financial advice
- I haven't backtested individual ticker strategies because small N makes that untrustworthy. The platform documents this limitation explicitly
- The lag-scan validates signal-to-return correlation, not a complete trading strategy

**Link to site:** [unstructuredalpha.com](https://unstructuredalpha.com)

Happy to discuss the methodology, the FRED series IDs used, or why certain signals were dropped. Also open to criticism of the validation approach — particularly the Bonferroni correction choice and whether cross-ticker pooling is valid for the insider/short-interest data.

---

*Not financial advice. Free to browse, Pro tier for alerts/AI features.*

---

---

## POST 2 — r/investing
**Flair:** Discussion / Tools

**Title:**
I published the full methodology behind my alternative data stock screener — including the signals that failed validation (most platforms hide this)

**Body:**
I've been building a project called Unstructured Alpha for the past several months. It's a dashboard that tries to answer one question: what are 38 alternative data series saying about a given stock, right now?

The data sources: FRED (macro + credit + energy), SEC EDGAR (Form 4 insider trades, 13F institutional filings, congressional trades), FINRA (biweekly short interest), EIA (crude/natural gas inventories), yfinance (price + earnings), plus VIX term structure, put/call ratio, and AI-scored FOMC transcripts.

Why I built it: I wanted to know when institutional insiders and macro signals were aligned before the price moved — rather than explaining it after. The academic literature on this (Seyhun 1986 on insiders, Asquith et al. on short interest, Brunnermeier/Nagel on institutional positioning) shows these signals carry real predictive content over 4-16 week horizons, but nobody had put them all together in a free, transparent tool.

What's different from TipRanks/SA Quant:
- The methodology is fully published on the site, including the exact FRED series IDs and statistical validation approach
- The Model Validation page shows which signals survived Bonferroni-corrected walk-forward validation, and which didn't
- It's built on entirely public, free APIs — reproducible by any researcher

**Current things the machine is flagging** (as of writing):
- HY credit spreads: elevated (bearish signal for risk assets broadly)
- Congressional trade momentum: net buying in defense/energy names
- 10-year yield: recent pullback slightly easing the headwind for rate-sensitive names

Free tier is fully functional for browsing signals and running screener searches. Pro adds personalized daily email alerts and some AI features.

**Site:** [unstructuredalpha.com](https://unstructuredalpha.com) | **Methodology:** About page

---

*This is not investment advice. Signals describe past relationships, not future certainties.*

---

---

## POST 3 — r/stocks
**Flair:** DD / Fundamentals

**Title:**
Alternative data screener I built: insider filings + institutional 13Fs + credit spreads + short interest, all normalized and scored per ticker [free tool]

**Body:**
I've been building this in my free time and figured it was at a point worth sharing.

**What it does:** Takes 38 data series from FRED, SEC EDGAR, FINRA, EIA, and yfinance, normalizes each one with a 52-week rolling z-score, and maps it to a 0-100 "Confluence Score" per ticker. The score represents whether the weight of alternative data evidence is bullish, bearish, or neutral for that stock.

**Signals that go into a typical ticker's score:**
- 10yr yield, HY/IG credit spreads, yield curve, TIPS breakeven (interest rate environment)
- Insider buying/selling ratio from Form 4 filings (via SEC EDGAR)
- Institutional positioning changes from 13F filings
- Short interest level and trend (FINRA semi-monthly data)
- VIX term structure, put/call ratio (market fear gauge)
- Congressional trade activity
- Fed sentiment from FOMC transcripts (AI-scored)
- EIA crude + natural gas data for energy names
- Earnings transcript sentiment (for the relevant quarter)

**What makes it different from just using StockCharts or a screener:**
It's not based on price at all. The idea is that price is the last thing to move — insider filings and credit spreads lead it. This is a hypothesis, not a proven fact, and the site explicitly documents where the signal validation failed.

**Important caveats (not glossed over):**
- Small N problem: for most tickers, there are fewer than 20 insider filing events — making the per-ticker correlation estimate noisy. I address this by capping insider/13F at 12% of the composite and using cross-ticker pooled lag-scans where possible.
- This is NOT financial advice
- Past signal relationships don't guarantee future ones

Free to use: [unstructuredalpha.com](https://unstructuredalpha.com)

---

---

## POST 4 — r/SecurityAnalysis
**Flair:** Tool / Resource

**Title:**
I built a free alternative data research platform with published methodology — 38 signals from FRED/SEC/FINRA/EIA, Bonferroni-corrected lead-time validation, Model Validation page that shows failures

**Body:**
Posting here because r/SecurityAnalysis tends to care about rigor over marketing, which is the right audience for this.

**Project:** Unstructured Alpha (unstructuredalpha.com)

**What it is:** A systematic signal research platform. Aggregates 38 alternative data series into per-ticker and macro-level Confluence Scores. The pipeline:

1. **Data ingestion:** FRED API (DGS10, BAMLH0A0HYM2, DCOILWTICO, M2SL, T10YIE, UMCSENT, NAPM, VXVCLS, etc.), EIA weekly supply data, SEC EDGAR Form 4 + 13F, FINRA biweekly short interest reports, yfinance
2. **Z-score normalization:** 52-week rolling mean/std. Removes level effects and makes signals comparable across wildly different underlying series
3. **Lag validation:** For each signal-ticker pair, I scan lags k = 1..16 weeks for peak Pearson |ρ| against forward equity returns. Bonferroni correction: threshold = 0.05/16. Signals also require OOS correlation ≥ 0.05 on a held-out 25% validation window
4. **Lag decay:** Every 30 days, the best-lag shifts and OOS correlation are recomputed on the trailing 104 weeks. Signals with lag drift > 4 weeks or OOS ρ < 0.03 are flagged as "decayed" and down-weighted
5. **Confluence aggregation:** Equal-weighted average of validated signals for the ticker. Insider/13F/short-interest capped at 12% each

**Where I'm honest about limitations:**
- Model Validation page publishes which signals failed each validation step — including those that looked great in-sample but didn't survive OOS
- Insider signal validation: cross-ticker pooled lag-scan required because per-ticker N is typically < 20. I've documented why this is statistically weaker than per-ticker analysis
- No complete trading strategy backtests — the Confluence Score is a research signal, not a backtest-ready alpha signal
- Known look-ahead bias risk: signal directionality was partly determined before seeing 2024-2025 data

**What's on the platform:**
- Signal Dashboard (real-time scores for all 38 signals)
- Ticker Deep Dive (signal → price overlay charts, factor exposure breakdown, AI explanation)
- Congress Tracker (real-time Form 4 congressional trades)
- Short Squeeze Radar
- Signal Backtester (custom signal combinations, walk-forward results)
- Model Validation page (the honest failures)

The methodology page on the site is detailed: it describes every formula, every statistical test, and every known weakness. I'd welcome criticism from this community — particularly on the cross-ticker pooling approach for insider data.

Free to use, Pro tier is $X/month for email alerts, AI features, and advanced analytics.

[unstructuredalpha.com](https://unstructuredalpha.com) — About page has the full methodology

---

*Not financial advice. Research and education only.*

---

---

## POST 5 — r/algotrading (follow-up / "Show HN"-style)
**Flair:** Project

**Title:**
Show r/algotrading: I built a macro regime detector using 38 FRED/EIA/SEC signals — it's been flagging elevated HY spreads as a headwind for 3 weeks [free]

**Body:**
Follow-up to a previous post about the methodology. Sharing because the platform has been live for a few months now and the macro signal state has been interesting.

**What the machine is currently reading** (at time of posting — check live dashboard for actual current values):

The High-Yield credit spread signal has been in bearish territory (elevated above the 52-week mean) for an extended streak. This signal has historically led broad equity softness by 4-8 weeks in the lag validation. Not a prediction, just context.

At the same time:
- The copper/gold ratio signal (a real-economy demand proxy) has been mixed/neutral
- Congressional trade activity has been net-positive in energy and defense names
- Short interest pressure has been building in a handful of tech/consumer names

**What this means for the platform design:**
One of the things I've been thinking about is how to avoid "regime dependence" — the problem where signals validated in 2010-2022 don't behave the same post-2022 because the macro environment changed. I've added a lag decay tracker that re-validates every 30 days, but that's a 30-day lag on detecting regime shifts. Working on faster decay detection.

**The platform:** [unstructuredalpha.com](https://unstructuredalpha.com)

Genuinely happy to discuss the underlying signal design, the lag validation methodology, or any specific signals. I'm also curious whether anyone has tried similar approaches and what they found worked/didn't work for the cross-ticker pooling problem.

---

*Not financial advice.*

---

---

## POSTING NOTES

**When to post each:**
- Post 1 (r/algotrading): Best on weekday mornings (8-10 AM ET). Technical, methodology-focused.
- Post 2 (r/investing): Tuesday-Thursday, 9 AM-12 PM ET. More accessible tone.
- Post 3 (r/stocks): Any weekday morning. Most accessible, broadest audience.
- Post 4 (r/SecurityAnalysis): Any time — this sub is slower, quality-focused.
- Post 5 (r/algotrading): After Post 1 has been up 1-2 weeks. Contextual follow-up.

**Rules to check before posting:**
- r/algotrading: No self-promotion without disclosure — always say "I built this"
- r/investing: Must post substantial content, not just a link. Rule 3: No self-promotion without value
- r/stocks: "DD" flair requires substance. Link to site is fine if body is detailed
- r/SecurityAnalysis: No spam/ads. Methodology rigor is respected here

**Responding to comments:**
- Welcome criticism of the validation methodology (it will come)
- Be ready to explain: why equal-weighted vs. ML-optimized weights, why Bonferroni vs. FDR, why tanh vs. sigmoid
- If asked for alpha: don't give specific trade recommendations. Redirect to the platform
- If asked about accuracy: point to Model Validation page and be honest about what "accuracy" means for a forward indicator

---

---

# BATCH 2 — REFERRAL + NEW FEATURES

---

## POST 6 — r/algotrading
**Flair:** Discussion / Project

**Title:**
I added a referral program to my macro signal dashboard — both sides get a longer trial. More importantly, I rebuilt the Track Record page to show every prediction the model made and whether it was right

**Body:**
Been working on Unstructured Alpha for a while (I've posted the methodology here before). Two updates worth sharing:

**1. Public Track Record page**

This is the one I'm most interested in feedback on. Every time a signal crosses a threshold on a watched ticker, the model logs a directional prediction (bullish/bearish) with a 4-week, 8-week, and 12-week forward window. When those windows close, the prediction auto-resolves against realized price data from yfinance.

The Track Record page shows:
- All predictions, resolved and pending, in a public feed
- Signal-level accuracy stats — which signals were right most often at which lead times
- High-confidence "the machine called it" cases where the Confluence Score was ≥70 and the prediction resolved correct

I specifically did NOT cherry-pick what shows up. The resolver runs on a nightly Render cron and marks correct/incorrect based purely on realized price return sign. The accuracy numbers are what they are.

Currently the win rate is decent on the 8-week window (where the validated lag-scan peaks for most macro signals) and worse on 4-week (shorter than the signals' lead times). That's consistent with the theory but small N means it's not statistically reliable yet.

**2. Referral program**

If you invite someone and they go Pro, you get a free month applied automatically via a Stripe coupon. People who sign up via your link get a 14-day trial instead of 7. No games — the mechanics are straightforward, the code is just Stripe coupon + trial_days parameter.

If you're curious about the methodology side — the signal construction, the walk-forward lag validation, the lag decay tracker — the About page has the full write-up.

[unstructuredalpha.com](https://unstructuredalpha.com)

*Not financial advice.*

---

---

## POST 7 — r/investing
**Flair:** Discussion

**Title:**
I built a Congressional trade tracker that cross-references congress members' Form 4 disclosures against my macro signal model — here's what it shows

**Body:**
Members of Congress are required to disclose trades within 45 days. Most tools just show you the raw disclosure data — "Senator X bought $50k of Nvidia on March 3rd." That's useful, but what I wanted to know is whether those trades were happening when macro signals were aligned.

So I built a Congressional Trade Tracker page that does two things:

**Raw disclosure feed:**
- Pulls congressional Form 4 data from SEC EDGAR
- Shows name, ticker, transaction type, dollar amount, filing date
- Filterable by name, ticker, party

**Cross-referenced with signal state:**
- For each disclosed trade, shows what the Confluence Score for that ticker was at the time of the trade
- Shows whether the macro signal environment (credit spreads, yield curve, insider activity) was bullish or bearish at that moment
- Flags cases where a congressional trade happened during high signal conviction (score ≥65 or ≤35)

What I've found: congressional trades tend to cluster in periods of signal ambiguity, not peak conviction. The high-conviction cases (score ≥70) are dominated by institutional 13F moves and insider cluster events, not congressional filings. Make of that what you will.

This is on the free tier — no account needed to browse it.

[unstructuredalpha.com](https://unstructuredalpha.com)

*Not financial advice. Congress trade data is public record from SEC EDGAR.*

---

---

## POST 8 — r/wallstreetbets
**Flair:** DD

**Title:**
I built a Short Squeeze Radar that combines FINRA short interest data + insider cluster detection + macro signal alignment — free to use [OC]

**Body:**
I know this sub has mixed feelings about "signal dashboards" so let me be direct about what this is and isn't.

**What it is:**
A screen that finds tickers where three things are happening simultaneously:
1. Short interest is elevated and RISING (FINRA biweekly data, z-scored against that ticker's 52-week baseline)
2. Insiders are BUYING — specifically, ≥2 Form 4 insider purchases within 21 days (I call this an "Insider Cluster")
3. The broader macro signal environment for that sector is NOT bearish

The thesis: short squeezes are more durable when insiders are buying into the squeeze and macro isn't working against you. This is not guaranteed, and there are plenty of examples where all three were true and the stock still fell.

**What it isn't:**
- It doesn't tell you when to buy or sell
- It doesn't predict squeeze timing
- The short interest data has a 2-3 week lag (FINRA publishes twice monthly)
- There's no "press button get alpha" functionality

**Current flags** (as of when I'm posting — check live for current):
The radar picks up 3-8 tickers on average on any given week. The false positive rate is real — not every flag squeezes. I've documented the base rate on the Model Validation page.

Free to use, no account needed to view the radar:
[unstructuredalpha.com](https://unstructuredalpha.com)

*Not financial advice. Short interest data is public from FINRA. Past signal relationships don't predict future ones.*

---

---

## POST 9 — r/stocks
**Flair:** DD

**Title:**
I added Score Velocity alerts to my alternative data dashboard — tracks how fast a stock's macro signal score is changing, not just where it is [free tool I built]

**Body:**
Most signal scoring systems give you a snapshot: "this stock scores 68/100." What I kept missing was the *rate of change* — a stock at 68 that was at 42 three weeks ago is very different from a stock at 68 that's been there for months.

So I built Score Velocity tracking. Here's how it works:

**The math:**
- Every day, the system logs the Confluence Score for every ticker in the database (sourced from the 38-signal macro pipeline)
- Score Velocity = slope of a linear regression over the trailing 30-day score window
- This gives a "pts/day" figure that's smoothed (not just a point-to-point difference)

**The alert:**
When a ticker's velocity is in the top 10% of its own 90-day velocity history — i.e., it's moving faster than it has in 3 months — you get an email alert. The threshold is relative, not absolute, so it fires for tickers at any score level.

**Why this matters more than the score itself:**
The lag validation shows macro signals lead returns by 4–12 weeks. If a score is *moving fast*, you may be earlier in that lead window than if you're looking at a stagnant high score.

**The honest caveat:** I've only been running this for a few months so there are no long-run backtests on velocity-triggered alerts specifically. It's a promising feature I'm still validating.

Free to browse scores and velocity. Email alerts are on the Pro tier.

[unstructuredalpha.com](https://unstructuredalpha.com)

*Not financial advice.*

---

---

## POST 10 — r/personalfinance
**Flair:** Tools & Resources

**Title:**
I built a free tool that shows what institutional investors (13F filings), insiders (Form 4), and congressional members are buying across 80+ stocks — all from public SEC filings [I built this]

**Body:**
Everything this platform uses is public data — the SEC mandates all of it. But pulling it yourself is annoying: you'd need to write EDGAR XBRL parsers, clean the data, normalize it across quarters, and then somehow connect it to macro context (credit spreads, yield curve, etc.).

I did all of that. Here's what's publicly accessible with no account:

**From SEC EDGAR (parsed and updated daily/quarterly):**
- Form 4 insider transactions — every buy and sell by company officers and directors, with dollar amounts and whether it was open-market or option exercise
- 13F institutional filings — what hedge funds and big asset managers are buying/selling each quarter, at the position level
- Congressional trade disclosures — senators and representatives are required to disclose within 45 days

**From FINRA (updated twice monthly):**
- Short interest levels for 80+ stocks, normalized against each ticker's own history so you're seeing "high for this stock" not "high in absolute terms"

**From FRED (Federal Reserve Economic Data):**
- 18 macro series: 10-year yield, HY credit spreads, M2, TIPS breakeven, copper/gold ratio, yield curve, Michigan consumer sentiment, ISM PMI, and more

The free tier shows all of this. The Pro tier ($X/month or free if someone refers you) adds personalized daily email alerts when something on your watchlist moves.

I've been building this for about a year. The About page has the full methodology.

[unstructuredalpha.com](https://unstructuredalpha.com)

*Not financial advice. All data sourced from public government filings.*

---

---

## POST 11 — r/SecurityAnalysis (follow-up)
**Flair:** Tool / Resource

**Title:**
Update on my alternative data platform: added public prediction logging + auto-resolution, referral mechanics, and a lag decay tracker. The 8-week window is performing; 4-week is noise.

**Body:**
Posted the methodology here a while back. Sharing an update since this community cares about intellectual honesty more than marketing.

**What's new and worth discussing:**

**Prediction logging + auto-resolution:**
Every signal threshold crossing now logs a directional prediction with a timestamp. The nightly cron resolves it once the 4w/8w/12w window closes, using realized price return sign as the outcome. No cherry-picking — every logged prediction appears on the Track Record page.

The 8-week window is running meaningfully above 50%. The 4-week window is effectively random — which is what I'd expect given the lag validation peaked at 5–9 weeks for most macro signals. Still small N (a few hundred resolved predictions), so confidence intervals are wide.

**Lag decay monitoring:**
Every 30 days, the validation runs on the trailing 104 weeks and checks if the best-lag has drifted > 4 weeks or if OOS ρ has dropped below 0.03. Three signals have triggered the decay flag in the last 90 days — they're still included but weighted down. I'm publishing which ones on the Model Validation page.

**Cross-ticker pooling update:**
For Form 4 insider signals, I've moved to a sector-pooled lag scan because per-ticker N is just too small. This introduces some cross-contamination risk (a tech insider's behavior might not generalize to all tech tickers) but it beats the alternative of fitting on 15-20 data points per ticker.

**Referral program:**
Standard Stripe mechanics. Mentioned only because some of you have shared the platform and I wanted the reward structure documented. Referee gets a 14-day trial; referrer gets 1 free Pro month per conversion.

Open to criticism on the cross-ticker pooling decision specifically. That's the most questionable methodological choice in the current system.

[unstructuredalpha.com](https://unstructuredalpha.com)

*Not financial advice. Research only.*

---

---

## POST 12 — r/quant
**Flair:** Discussion

**Title:**
Lag decay monitoring for a live macro signal system — what I learned after 90 days of production data

**Body:**
I've been running a 38-signal macro alternative data system in production for a while now. After adding automated lag decay monitoring (revalidate signal lead times every 30 days on trailing 104 weeks), I wanted to share what I'm actually seeing because I couldn't find many practical write-ups on this topic.

**Setup:**
- Signals: FRED series, EIA energy data, SEC EDGAR Form 4/13F, FINRA short interest, VIX structure, put/call ratio, AI-scored FOMC transcripts
- Validation: walk-forward lag scan (k=1..16 weeks), Bonferroni correction (α/m = 0.05/16), OOS ρ ≥ 0.05 on held-out 25% window
- Decay detection: monthly revalidation on trailing 2-year rolling window. Decay = best-lag shift > 4 weeks OR OOS ρ < 0.03

**What I've seen in 90 days:**

*Stable signals:*
- HY credit spreads: best-lag consistent at 6–8 weeks, OOS ρ stable ~0.18
- 10-year yield: stable at 4–6 weeks
- TIPS breakeven: stable at 5–7 weeks

*Decayed signals:*
- Michigan Consumer Sentiment: best-lag shifted from 6 weeks → 2 weeks over the past year. Still significant but borderline on OOS
- Copper/Gold ratio: OOS ρ dropped to 0.02 in the last revalidation — currently flagged and down-weighted
- Congressional trades: inconsistent across sectors, pooled lag unstable. This one might need a different approach

*Never validated (excluded from composite):*
- ISM PMI: in-sample ρ significant but OOS was ~0 on every window I tested. Classic overfit — the series has structural breaks that make rolling validation unstable

**What I'd do differently:**
I'd add faster decay detection (14-day rolling instead of 30-day) for signals that trade on behavioral data (congressional, insider). These are more susceptible to regime change than FRED macro series.

Happy to discuss the revalidation window choice or the pooling approach for event-based signals.

[unstructuredalpha.com/About](https://unstructuredalpha.com) — full methodology

*Not financial advice. Research only.*

---

---

## POST 13 — r/algotrading (referral angle)
**Flair:** Discussion

**Title:**
The referral mechanics I built for a quant dashboard: 14-day trial extension + Stripe coupon reward — implementation notes and why I structured it this way

**Body:**
I see a lot of posts here about building subscription products alongside trading tools. Thought I'd share how I structured the referral program for Unstructured Alpha since it has a couple of non-obvious design decisions.

**The mechanics:**
- Referral code lives as a column on the users table (8-char URL-safe alphanumeric, generated on first view of the share page)
- Referral link: `unstructuredalpha.com/Upgrade?ref=CODE`
- When someone signs up via that link: `trial_days=14` is passed to `stripe.checkout.Session.create()` instead of the default 7. The trial extension is enforced by Stripe, not by us — we can't accidentally grant it twice
- When the referee converts to paid: a `ua_referral_1mo_free` Stripe coupon (100% off, `duration=once`) is applied to the referrer's active subscription via `stripe.Subscription.modify(sub_id, coupon=COUPON_ID)`
- The coupon is a reusable server-side object. We create it once, Stripe handles the rest

**Why 14 days vs a discount:**
Trial extension feels more honest than a percentage discount. You're not manufacturing urgency around a fake price — you're just giving someone more time to evaluate. Anecdotally, longer trials convert at similar rates to shorter trials on B2C SaaS, because the decision to convert is about value clarity, not urgency.

**Why 1 month vs cash:**
1 free month has higher perceived value than its cash equivalent for existing subscribers. It's also simpler — no payout infrastructure, no minimum thresholds, no 1099s for <$600 aggregate.

**The honesty version:** I have no idea if this referral program will actually move signups. It's implemented correctly but I don't have enough data yet to say it performs. Mentioning it here because the implementation details might be useful to others building similar systems.

[unstructuredalpha.com](https://unstructuredalpha.com)

*Not financial advice.*

---

---

# TWEET TEMPLATES

## CATEGORY: Referral Program

**Tweet R1 — announcement:**
Refer a friend to Unstructured Alpha → they get 14 days free (vs 7), you get 1 month free when they go Pro.

No codes to manage. Your link is at unstructuredalpha.com → Upgrade → Share.

38 macro signals. Free to browse.

**Tweet R2 — soft ask:**
If you've found Unstructured Alpha useful, the referral program is live.

Your friend gets double the trial period. You get a free month.

Share your link from the Upgrade page.

unstructuredalpha.com

**Tweet R3 — value prop first:**
14 days to evaluate 38 signals, congressional trades, insider clusters, and short squeeze radar.

That's what a referred signup gets.

Existing users: your referral link is on the Upgrade page.

---

## CATEGORY: Daily / Rotating Product Hooks

**Tweet P1 — Congressional trades:**
Congressional trade disclosures are public. We normalize them.

The Congressional Trade Tracker on Unstructured Alpha cross-references Form 4 disclosures against the 38-signal macro environment at the time of each trade.

Free to browse: unstructuredalpha.com

#investing #congress

**Tweet P2 — Short Squeeze Radar:**
The Short Squeeze Radar looks for:

🔴 Short interest elevated + rising (FINRA)
🟢 ≥2 insiders buying within 21 days (SEC Form 4)
📊 Macro environment not bearish

When all three align, it flags.

Free: unstructuredalpha.com

#stocks #shortsqueeze

**Tweet P3 — Track Record:**
Every threshold crossing logs a prediction.

Every prediction auto-resolves against realized price data.

The Track Record page shows all of it — correct, incorrect, pending.

No cherry-picking.

unstructuredalpha.com/Track_Record_Live

**Tweet P4 — Score Velocity:**
A stock at a score of 68 that was at 42 last month is different from one that's been at 68 for 90 days.

Score Velocity = rate of change of the Confluence Score.

Top-10%-of-own-history velocity triggers an alert.

unstructuredalpha.com

**Tweet P5 — Model Validation (honesty angle):**
The Model Validation page publishes the signals that failed validation.

Including which ones looked good in-sample but didn't survive the out-of-sample window.

Most platforms don't publish their failures.

unstructuredalpha.com/Model_Validation

#quant #algotrading

**Tweet P6 — Macro narrative hook:**
43 signals. 1 question: is the macro environment net bullish or bearish right now?

The Signal Dashboard breaks it down by category: credit, energy, positioning, sentiment, earnings.

Free: unstructuredalpha.com

**Tweet P7 — Insider Cluster:**
An "Insider Cluster" = 2+ company insiders buying open-market shares within 21 days.

The research literature treats clusters as more signal-rich than single purchases.

Unstructured Alpha badges them automatically from SEC Form 4 data.

unstructuredalpha.com

**Tweet P8 — Data provenance:**
Data sources powering Unstructured Alpha:

📡 FRED — 18 macro series
🏛️ SEC EDGAR — Form 4 (insiders), 13F (institutions), congressional trades
📊 FINRA — biweekly short interest
⛽ EIA — crude & nat gas inventories
🤖 Anthropic — FOMC sentiment scoring

All public. All free tier.

unstructuredalpha.com

**Tweet P9 — Stress Tester:**
What happens to your portfolio's macro exposure if the yield curve inverts further?

The Macro Scenario Stress Tester lets you shift signal inputs and see how your watchlist scores would move.

Pro feature: unstructuredalpha.com

**Tweet P10 — Machine's Best Ideas hook:**
Today's Machine's Best Ideas: tickers where the Confluence Score is ≥65 AND rising.

Score + velocity combined into a rank.

Updated daily. Free to view.

unstructuredalpha.com/Best_Ideas

---

## CATEGORY: Methodology / Credibility

**Tweet M1:**
Why Bonferroni correction instead of FDR for the signal lag validation?

Because we're testing 16 lags per signal and the cost of including a spurious signal (model noise) > cost of excluding a marginal one (missing coverage).

FDR is better when you want discovery. We want precision.

**Tweet M2:**
The lag scan finds the lead time at which each macro signal best predicts forward equity returns.

For HY credit spreads: ~6-8 weeks.
For insider cluster events: ~4-6 weeks.
For FOMC sentiment: ~5-7 weeks.

These shift. We re-check every 30 days.

**Tweet M3:**
Three signals have triggered the lag decay flag in the past 90 days.

When a signal's best-lag shifts >4 weeks OR out-of-sample ρ drops below 0.03, it's down-weighted.

The Model Validation page lists which ones and why.

unstructuredalpha.com/Model_Validation

**Tweet M4:**
The Confluence Score does NOT claim to predict stock prices.

It aggregates what 38 independent alternative data series are saying, normalized, validated, and mapped to a 0-100 scale.

That's it. The interpretation is yours.

**Tweet M5:**
We use tanh(z/2) × 30 + 50 to map z-scores to the 0-100 scale.

Why tanh instead of a linear cap?
→ Smooth at the extremes (avoids hard clipping)
→ Bounded without cutoffs
→ Preserves the ordinal relationship

Full methodology: unstructuredalpha.com/About

---

## CATEGORY: Community Engagement / Hooks

**Tweet C1:**
What alternative data do you think is underrated as a retail-accessible signal?

Our list: HY spreads, Form 4, 13F, FINRA short interest, EIA, FOMC text, put/call ratio.

What would you add?

**Tweet C2:**
If you had to pick ONE macro signal to watch for the next 6 months, what would it be?

(For us it's HY credit spreads. It's been the most consistently validated at the 6-8 week horizon.)

**Tweet C3:**
Hot take: the hardest part of building an alternative data platform isn't the data.

It's figuring out what "this signal works" actually means and being honest when it doesn't.

**Tweet C4:**
The Model Validation page publishes every signal that failed our walk-forward test.

ISM PMI: looked great in-sample. OOS ρ ~0 on every window. Excluded.

Copper/Gold: decayed over the last 90 days. Currently down-weighted.

This is what transparency looks like.

---

## POSTING SCHEDULE (Tweets)

**Daily (auto via cron — already live):**
- 9 AM ET: Signal flip digest (@tweet_signal_flips)
- 10 AM ET: Machine's Best Ideas (@tweet_best_ideas)

**Manual rotation (post 3-4x/week):**
- Monday: Tweet M1 or M2 (methodology — sets intellectual tone for week)
- Tuesday: Tweet P1 or P7 (product feature — congressional/insider hook)
- Wednesday: Tweet C1 or C2 (community engagement question)
- Thursday: Tweet P3 or P5 (Track Record / Model Validation — honesty angle)
- Friday: Tweet R1 or P2 (referral or short squeeze — higher virality potential)

**Referral push (run for 2 weeks after launch):**
- Post R1, R2, R3 on alternating days. Don't hammer it — once every 3-4 days max.

---

## SUBREDDIT SCHEDULE (Batch 2)

- Post 6 (r/algotrading — Track Record + referral): Post after Track Record page has 100+ resolved predictions
- Post 7 (r/investing — Congressional trades): Any weekday morning, 9-11 AM ET
- Post 8 (r/wallstreetbets — Short Squeeze Radar): Post when a live squeeze is developing for maximum relevance
- Post 9 (r/stocks — Score Velocity): Tuesday-Thursday, 9 AM-12 PM ET
- Post 10 (r/personalfinance — public data tool): Weekend morning — this sub peaks Saturday
- Post 11 (r/SecurityAnalysis — methodology update): Any time, this sub is quality-gated not time-gated
- Post 12 (r/quant — lag decay): Technical deep-dive, post during a US market morning
- Post 13 (r/algotrading — referral mechanics): Only after Post 1 or 6 has been received well
