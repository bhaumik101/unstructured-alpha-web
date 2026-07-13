# Unstructured Alpha — 30-Day Twitter/X Content Calendar
*Account: @UnstAlpha | Theme: transparent, data-driven, solo builder*
*Mix: ~40% educational signal explainers | ~30% data observations | ~20% product | ~10% engagement*

---

## Week 1 — Signal Foundation

**Day 1 (Mon)**
The yield curve (10Y–2Y) just turned positive for the first time in 18 months.

That's the signal on our dashboard right now: Bullish, score 71/100.

What does it mean? Historically, the un-inversion precedes a risk-on shift by 3–6 months — not immediately. The lag matters.

→ unstructuredalpha.com/Signal_Dashboard

---

**Day 2 (Tue)**
Most stock platforms will tell you to buy or sell NVDA.

We just tell you the macro backdrop: credit spreads tight, insider buying elevated, EIA crude draws bullish for energy names, ISM PMI borderline.

Score: 74/100. You decide what to do with it.

→ unstructuredalpha.com/Ticker_Deep_Dive

---

**Day 3 (Wed) — Educational**
How the CBOE Put/Call Ratio works as a signal:

- Below 0.7: too much call buying → contrarian bearish
- Above 1.2: panic/put buying → contrarian bullish
- Current reading: 0.84 (neutral, score 53)

It's a sentiment extreme detector, not a directional predictor. The difference matters.

---

**Day 4 (Thu)**
Insider buy clusters on the dashboard this week:

3+ officers buying within 21 days in the same ticker gets flagged. Not every cluster matters — but clusters in sectors with macro tailwinds historically have better outcomes.

Current tagged tickers: [check the live dashboard]

→ unstructuredalpha.com/Ticker_Deep_Dive

---

**Day 5 (Fri) — Product transparency**
Our Model Validation page publishes the out-of-sample backtest for every signal, including the ones that don't hold up.

Most platforms hide the failures. We don't. Here's why:

If you can't see which signals actually work, you're flying blind. Transparency is the product.

→ unstructuredalpha.com

---

**Day 6 (Sat) — Engagement**
What's the one data point you check every morning before markets open?

Mine is the 10Y yield + HY credit spread spread. Together they tell me more about risk appetite than any single indicator.

---

**Day 7 (Sun)**
Weekly macro brief is out.

What moved this week:
▲ Insider Buy Ratio: up 8 pts — elevated cluster activity
▲ TIPS Breakeven: up 4 pts — market pricing more inflation
▼ ISM PMI: down 5 pts — borderline contraction

Full brief: stocks.unstructuredalpha.com/brief

---

## Week 2 — Credibility + Differentiation

**Day 8 (Mon)**
The copper/gold ratio just crossed above 0.25.

Why it matters: copper prices are tied to industrial demand; gold is tied to risk-off sentiment. When copper outperforms gold, it historically signals growth expectations are improving.

Current signal: Bullish, 68/100. Watching.

---

**Day 9 (Tue) — Compare**
Bloomberg Terminal: ~$27,000/year
Seeking Alpha Quant: hides methodology
TipRanks: black-box composite scores

Unstructured Alpha: $20/month, full methodology, published validation, 38 signals from public data

Not the same product. But same question being answered: "What does the data say?"

---

**Day 10 (Wed) — Educational**
How FINRA short interest data becomes a signal:

1. Pull biweekly short interest from FINRA
2. Normalize by float
3. Score on rolling 1-year percentile (0–100)
4. A score above 70 = historically elevated short interest for that ticker

It's not "squeeze imminent" — it's "pressure is building." Context + other signals determine what that means.

---

**Day 11 (Thu)**
Signal streak tracker feature: how many consecutive periods has a signal stayed bullish or bearish?

Long streaks can mean two things:
1. Strong macro regime that's persisting
2. Signal fatigue — the information content decays

We flag both. A 6-month bullish streak is different from a 3-week one.

---

**Day 12 (Fri) — Behind the scenes**
Things I didn't expect building this:

1. Signal validation is harder than signal construction
2. Bonferroni correction kills about 30% of "significant" lags
3. Users want transparency more than they want predictions
4. The boring infrastructure (DB, caching, crons) takes 10x longer than the fun stuff

---

**Day 13 (Sat)**
The Michigan Consumer Sentiment index is often dismissed as "too lagging."

But our lag scan shows it has a 4–8 week lead time on consumer discretionary sector performance when it crosses below 65.

It's currently at 67. Watching.

---

**Day 14 (Sun)**
If you've been following Unstructured Alpha for a while:

What would make the platform more useful to you? One feature, one improvement. Drop it in replies.

Genuinely asking — this is a solo project and your feedback drives the roadmap.

---

## Week 3 — Depth + Product Education

**Day 15 (Mon)**
The VIX term structure is one of the most underrated macro signals.

When VIX9D > VIX30 (contango): near-term fear > long-term → typically short-lived selloffs
When VIX30 > VIX9D (backwardation): structural anxiety, not panic → more persistent weakness

Current structure: flat, score 52 (neutral).

---

**Day 16 (Tue)**
Confluence Score explained simply:

For each ticker, we find which signals historically correlate with its 4–12 week returns.

Weight those signals by correlation strength + statistical significance.

Score them on a 0–100 scale vs. their 1-year percentile.

That's it. No neural nets. No black box. Just weighted, validated correlations.

---

**Day 17 (Wed) — Data source education**
We pull from 7 public primary sources. Here's what each one actually gives us:

FRED: macro series (rates, spreads, money supply, PMI)
SEC EDGAR: Form 4 insider transactions, 13F institutional holdings
FINRA: biweekly short interest by ticker
EIA: weekly crude oil + gas storage inventories
CBOE: put/call ratio, VIX term structure
Yahoo Finance: price data for scoring
Congress API: congressional trade disclosures

All public. All free-access. No proprietary data.

---

**Day 18 (Thu)**
Energy signal check:

EIA crude inventory: bearish (draw streak ended)
Rig count: neutral (still below COVID-era highs)
Natural gas storage: bullish (below 5-year avg)

Sector composite: Neutral → Bullish transition. Watching LNG and E&P names for the flip.

→ Live scores: unstructuredalpha.com/Signal_Dashboard

---

**Day 19 (Fri) — Honest take**
What we can't do:

- Predict short-term price moves
- Catch every macro turn in real time
- Replace your own research and judgment

What we can do:

- Tell you the state of 38 macro/alternative data signals right now
- Show you which signals historically matter for your specific ticker
- Be transparent about when signals don't work

The goal is better context, not a crystal ball.

---

**Day 20 (Sat)**
One of the most surprising findings from building the signal backtester:

The ISM Manufacturing PMI crossing 50 (contraction to expansion) has a stronger historical signal for industrial names than any of the price-based momentum signals.

And yet it's almost never mentioned in mainstream investment coverage.

---

**Day 21 (Sun)**
Weekly brief is out. Signal of the week:

TIPS Breakeven Inflation (10Y) crossed 2.4% this week.

That's the market pricing in above-Fed-target inflation for the next decade. What it means for sectors: real assets, energy, and industrials historically outperform in this regime.

Full brief: stocks.unstructuredalpha.com/brief

---

## Week 4 — Community + Launch Energy

**Day 22 (Mon) — Pre-PH teaser**
Something is coming Thursday.

We're launching on Product Hunt. 

38 macro signals. Model validation published in full. Free to start.

If you've been using Unstructured Alpha and found it valuable — your upvote on Thursday would mean a lot to a solo builder.

---

**Day 23 (Tue)**
The signal that most surprised me when I built it:

The Copper/Gold Ratio.

Simple: (copper price) / (gold price). No fancy math.

But its historical correlation with forward equity returns in cyclical sectors is remarkably consistent. And it's public data, freely available, that almost nobody tracks systematically.

---

**Day 24 (Wed) — PH Eve**
Tomorrow: launching Unstructured Alpha on Product Hunt.

Three things I want you to know before you check it out:

1. The Signal Dashboard is completely free
2. Every score comes with its validation status
3. I built this because I was tired of black-box ratings with no methodology

See you tomorrow.

---

**Day 25 (Thu) — LAUNCH DAY**
We're LIVE on Product Hunt 🚀

Unstructured Alpha: 38 independent macro signals, scored daily from FRED, SEC EDGAR, FINRA, EIA, and CBOE.

The thing I'm most proud of: every score publishes its validation results, including the ones that failed.

→ [PRODUCT HUNT LINK]

If you've found this useful — an upvote takes 10 seconds and helps a solo builder more than you know. 🙏

---

**Day 26 (Fri) — PH thank you**
We ended Day 1 on Product Hunt at [rank].

To everyone who upvoted, commented, and shared: genuinely thank you.

Building this in the open has been the best decision I've made. The feedback I got in the first 24 hours will shape the next 3 months of the roadmap.

---

**Day 27 (Sat) — Engagement**
What's your process for macro context before sizing into a position?

Mine used to be: read two conflicting Seeking Alpha articles and flip a coin.

Now it's: check the signal dashboard, look at the confluence score for the sector, see if insider activity aligns.

What's yours?

---

**Day 28 (Sun)**
Weekly brief: the three signals that moved the most this week.

Every Sunday, the narrative engine generates a plain-English read on what changed and why.

Free, no login required.

→ stocks.unstructuredalpha.com/brief

---

**Day 29 (Mon) — Educational**
Congressional trading disclosures are public within 45 days of a trade.

We pull them via the Quiver Quant API and surface them in the dashboard alongside company insider (Form 4) data.

The question isn't "should politicians be trading" — the question is: if they are, does it tell you anything about macro sector conviction? Our data suggests: sometimes.

---

**Day 30 (Tue) — Reflection**
30 days of signal posts.

What I've learned: the audience that cares about transparent, honest macro tooling is real and engaged. You push back when something's wrong. You ask good questions.

That's the product I want to build.

Next 30 days: [tell me in replies what you want to see more of]

---

## Notes for scheduling

- Best posting times: 8–9 AM ET (pre-market) and 4:30–6 PM ET (after-market close)
- Weekend posts: Saturday 10 AM, Sunday 11 AM
- Launch day (Day 25): post at 12:01 AM PT for Product Hunt + 8 AM ET for Twitter
- For posts with "live data," check the dashboard that morning and fill in actual current readings
- Add screenshots of the dashboard to any post where you mention a specific score/signal reading
- Engage with replies within 2 hours of posting — algorithm rewards early engagement

---

## Hashtag rotation (use 2–3 per post, not all)

`#quant` `#investing` `#stocks` `#macroeconomics` `#algotrading`
`#signaltrading` `#activeinvesting` `#FRED` `#stockmarket` `#ProductHunt`
