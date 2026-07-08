# Social Media Batch 3 — Unstructured Alpha
# July 2026 — Execute this week

---

## PART 1: REPLY TO LIVE r/SideProject COMMENTS (DO FIRST — thread is 22h old)

Your post: https://www.reddit.com/r/SideProject/comments/1uomzv6

---

### Reply to Key-Chocolate-2147 (asked about amended/delayed STOCK Act filings):

> Great question — this is actually one of the trickier parts. STOCK Act filings are supposed to come within 45 days but in practice a lot get filed late, and amendments (Form 8-K/LD updates, or amended PTR filings for Senate) can come weeks after the original.

> The way I handle it: every filing gets stored with both a `transaction_date` and a `filed_date`, and the signal engine only uses `filed_date` as the "as of" timestamp when computing lead time. So if a congressman bought XYZ on March 1 but filed on April 10, the platform treats it as a March → April 10 signal, not a March → April 1 signal. This prevents the common mistake of making the signal look more predictive than it actually is.

> Amendments I handle with a de-dupe + replace — when an amendment comes in for an existing filing ID, it overwrites the original record and re-timestamps with the amendment filed date, not the original. Means the score can update retroactively which is technically impure but more accurate than ignoring amendments entirely.

> Still not perfect — there's no great way to know a filing will be amended before it happens. But flagging "filing lag > 30 days" on the Congress Tracker UI at least makes the late ones visible.

---

### Reply to _suren (Top 1% Commenter — raised "known as of date" concern):

> This is exactly the right concern and you're correct that most dashboards in this space get it wrong. The confluence score on my platform uses filed_date throughout — every signal is timestamped to when the data became publicly observable, not the underlying event date.

> For insiders: transaction date vs. filed date (SEC requires Form 4 within 2 business days but they frequently come later). For FINRA short interest: I use the publication date, not the settlement period end date — about a 2-week lag built into the data already. For EIA: the report release date, not the week ending date. These are all "as of" the moment a real trader could have seen it.

> I display the data lag on the signal card itself — e.g. "FINRA Short Interest (data lags ~2 weeks)" — so users know they're not seeing something in real time. The Model Validation page also explicitly notes these lags in the out-of-sample testing methodology: the OOS window uses only data that would have been available at each point in time.

> The audit trail page (each filing links back to its SEC EDGAR or STOCK Act source URL) was specifically built to let users verify this themselves rather than taking my word for it.

---

## PART 2: NEW REDDIT POSTS (subreddits we haven't hit yet)

---

### POST 9 — r/SecurityAnalysis
**Post 7–10 days from now. Build karma there first by commenting on 2–3 DD threads.**
**Flair: Discussion**

**Title:**
How I validate whether alternative data actually leads stock returns — and what failed

**Body:**
r/SecurityAnalysis seems like the right place to share this, since the bar here is actually thinking rigorously about what has and hasn't been validated.

I've been building a system that cross-correlates 47 macro and event-driven signals against forward equity returns. The validation methodology:

**How I test:**
For each signal × ticker pair: lag scan from 1–16 weeks, Spearman rank correlation, Bonferroni correction at alpha/16 ≈ 0.003, then a held-out OOS window (final 25% of data never seen during fitting). A signal only "passes" if it survives both — in-sample AND OOS.

Without Bonferroni I was finding 20–30 "significant" predictors per ticker. With it: usually 2–5 that survive to OOS.

**What passed OOS:**
- Insider buying clusters (2+ Form 4 filers from same company within 21 days) — strongest when it appears, but N per name is small
- HY credit spread widening → risk-off in equities at 4–6 week lag. Consistent across sectors.
- EIA crude inventory draws → energy sector outperformance at 3–5 weeks. Specific to energy names.
- Yield curve slope → meaningful at index/sector level, not individual stock level
- Congressional trade clusters (3+ members in same name within 45 days) — preliminary, not enough OOS data yet

**What failed OOS completely:**
- Social sentiment (Google Trends, StockTwits volume) — looks predictive in-sample on almost anything. Falls apart OOS systematically.
- Single commodity signals standalone — gasoline, copper, lumber. Classic overfitting — too specific, regime-dependent.
- Short interest alone — not predictive of forward returns. Short interest + macro alignment + insider cluster: different story.
- Most 13F positioning signals — the disclosure lag (45 days) is too long for the signal to be actionable.

All results are published on a Model Validation page at unstructuredalpha.com/Model_Validation. Happy to discuss the methodology — particularly curious if anyone here has found better ways to handle the N=small problem with insider clusters.

---

### POST 10 — r/thetagang
**Great fit — options sellers love macro regime context for selecting strikes/timing.**
**Post after r/stocks has some traction. No flair needed.**

**Title:**
I built a macro regime dashboard that helps me decide when to be more aggressive with premium selling vs. when to tighten up

**Body:**
Context: I've been selling cash-secured puts and covered calls for a while, and I kept running into the same problem — my entry timing was pure vibes. IV rank told me *whether* to sell premium, but not *what the macro backdrop* was for the underlying.

So I built unstructuredalpha.com — a dashboard that tracks 47 macro signals and produces a daily "confluence score" showing how many independent signals are aligned bullish or bearish for a given stock.

**How I actually use it for thetagang strategies:**

*Before selling CSPs:* I check the confluence score for the underlying. If it's reading bearish macro context (credit spreads widening, insider selling clusters, poor sector rotation), I either skip it, go much further OTM, or reduce position size. The dashboard has caught a few situations where I would have sold puts right before a sector-level move.

*For covered calls:* Bullish confluence score on the name = I'm more conservative with strikes (go further OTM, don't cap the upside too aggressively). Bearish score = I'm fine selling closer to the money since I want the assignment risk to push me out.

*What I watch most:* HY credit spreads and the VIX term structure signal. When HY spreads are tightening and VIX term structure is in contango (longer-dated VIX > short-dated), it's historically a favorable backdrop for premium selling. When those flip, I pull in my risk.

**Right now (July 2026):** VIX term structure just flipped bullish this week. HY credit spreads near multi-year lows. Yield curve positive (+31bps). 13 bullish / 8 bearish / 26 neutral signals. Generally a favorable backdrop for premium selling, though the mixed reading means I'm not going max aggro.

Most pages are free — you don't need an account to browse the Signal Dashboard or Today's Brief. The Short Squeeze Radar is also useful for avoiding names with elevated squeeze risk when selling puts.

unstructuredalpha.com

---

### POST 11 — r/MacroEconomics
**On-topic sub. Pure value post, minimal product push.**
**Best timing: Monday/Tuesday after a macro data release**

**Title:**
The yield curve re-steepened to +31bps. Historically, what happens to equities 6–12 months after the first positive close after a long inversion?

**Body:**
The 10Y/2Y spread closed positive for the first time since mid-2022 in late 2024 and has been widening since — currently +31bps (10Y: 4.38%, 2Y: 4.07%).

This is historically one of the more interesting macro inflection points. The conventional reading is: yield curve inversion = recession signal, re-steepening = recovery. But the actual historical pattern is more nuanced.

**What the data shows:**
Re-steepening after long inversions has historically been *late-cycle*, not early-cycle. The recession often comes *after* the curve re-steepens, not before or during the inversion. The 2000 and 2007 cycles both had the curve go positive before equities peaked.

What matters is *why* it's re-steepening: bull steepening (long rates falling, Fed cutting) vs. bear steepening (long rates rising faster than short rates). Currently we're in a mild bear steepening — 10Y rising slightly faster than 2Y. Historically that's different from a bull steepen and tends to be less bullish for equities.

**Signals that typically confirm the macro backdrop alongside re-steepening:**
- HY credit spreads: currently near multi-year lows, no credit stress
- Jobless claims: 215K as of last week, 4wk MA ~223K — labor market resilient
- ISM PMI: borderline but not in contraction
- EIA crude draws: 7 consecutive weekly draws — demand still there

The confluence of positive yield curve + tight credit spreads + resilient labor = broadly supportive for risk assets near-term. The late-cycle risk is the part to watch 6–12 months out.

I track all of this at unstructuredalpha.com if anyone wants to see the signal dashboard — most is free without an account.

Curious what this sub thinks about the late-cycle re-steepen thesis vs. the "soft landing continuation" read.

---

### POST 12 — r/Python
**Technical build angle. Python builders love this kind of post.**
**Flair: Project**

**Title:**
Built a 28-page financial dashboard in Python/Streamlit — here's the architecture, the hard parts, and what I'd do differently

**Body:**
I've been building Unstructured Alpha (unstructuredalpha.com) for about 6 months and wanted to share some architectural notes for anyone building data-heavy Streamlit apps.

**What it does:** Pulls 47 alternative data signals (FRED, EIA, SEC EDGAR, FINRA, CBOE) and cross-correlates them against equity returns using lag scans. 28 pages total, PostgreSQL backend, Render for hosting.

**The hard parts:**

*1. Caching strategy is everything.*
Streamlit's `@st.cache_data` with TTLs is great but you have to be deliberate. I ended up with a 2-hour cache for the full signal computation, a 60-second cache for the live ticker strip, and a 24-hour cache for the lag-scan results (expensive to recompute). Using `max_entries=1` on the expensive caches to prevent memory bloat under concurrent users.

*2. Concurrent users with Streamlit is trickier than it looks.*
Streamlit runs each user session in a separate thread but shares module-level state. Any mutable global → race condition. Solution: everything goes through `st.session_state` or the DB. No shared in-process state.

*3. SEC EDGAR Form 4 XML parsing.*
SEC EDGAR is XML but the schema is inconsistently applied across filings. The `derivative_table` vs. `non_derivative_table` split, amended filings overwriting originals, and the `transaction_code` field (P = purchase, S = sale, F = tax withholding) all need careful handling. I parse with `xml.etree.ElementTree`, not BeautifulSoup — faster and strict enough that malformed filings error out instead of silently producing garbage data.

*4. Bonferroni correction across 16 lags per signal × equity pair.*
With 47 signals × many tickers × 16 lags, multiple comparisons is a real problem. Harvey, Liu & Zhu (2016) is the reference. Implementation: `scipy.stats.spearmanr` per lag, then `alpha_corrected = 0.05 / 16` per pair, then a separate OOS split. The OOS window is the key — everything else is just a hurdle.

*5. Streamlit pagination.*
28 pages with `st.navigation` + `st.Page`. The sidebar customization requires CSS injection because Streamlit doesn't expose it natively. All sidebar CSS lives in a shared `header.py` that every page imports.

**What I'd do differently:**
- FastAPI backend + React frontend for the interactive pages. Streamlit is great for shipping fast, but the WebSocket architecture means no server-side rendering and Chrome lighthouse scores are rough.
- Start with the DB schema before writing a single page. I migrated it 4 times.
- Write the caching strategy on day 1, not after the app slows down.

Live at unstructuredalpha.com. Repo isn't public but happy to answer specific architecture questions.

---

### POST 13 — r/startups
**Founder angle. r/startups loves "what I built and what I learned" posts.**

**Title:**
6 months of evenings → live fintech dashboard with real users. Here's what distribution actually looked like.

**Body:**
I want to share an honest account of what building and distributing a solo fintech side project actually looked like — because most "I built X" posts skip the hard part.

**The build (months 1–4):**
Python/Streamlit stack, PostgreSQL, Render hosting. 28 pages tracking 47 alternative data signals (FRED, EIA, SEC EDGAR, FINRA, CBOE). The core product: a per-ticker "confluence score" that aggregates macro signals validated against actual forward returns with Bonferroni correction and OOS testing.

**The distribution reality (months 4–6):**

*What didn't work:*
- Cold outreach to finance Twitter: zero response
- Posting on LinkedIn without building an audience first: near-zero
- r/algotrading (first attempt): removed by mods for new account

*What actually worked:*
- r/SideProject: genuine engagement, people asked real questions, some converted
- Hacker News "Show HN": modest upvotes but high-quality feedback from technical users
- r/investing and r/stocks data posts (not product posts): these drove actual signups because I was providing value first
- Building in public on Twitter even with almost no followers: the posts compound slowly but people find them

**The thing I underestimated:**
Distribution is 10x harder than building. Anyone can build a dashboard. Getting the right people to see it and trust it enough to try it is the actual work.

**The honest metrics:**
- 7-day free Pro trial
- Free tier browses most pages without an account
- Paying users: small but real and growing
- Most signups came from 2–3 Reddit posts, not the product itself

If you're building a fintech side project: get something live fast, post about it genuinely (not salesy), answer every comment. The compound interest on early community engagement is real.

unstructuredalpha.com — 7-day free Pro trial if anyone wants to check it out.

---

### POST 14 — r/options (high upside, mods are watch but good if value-first)
**Angle: free data tool for options positioning decisions.**
**Flair: Discussion**

**Title:**
Free dashboard I use to check macro context before entering options positions — breakdown of what I actually look at

**Body:**
Not a "here's my positions" post — sharing a tool I've built and use to inform my own options decisions. Happy to discuss the methodology.

unstructuredalpha.com tracks 47 macro and event-driven signals and synthesizes them into a daily macro regime read. Here's the 3 signals I look at most when entering options positions:

**1. VIX Term Structure**
When short-dated VIX (VIX9D) > longer-dated VIX = backwardation = market pricing in near-term fear. When the term structure is in contango (long-dated > short-dated) = calmer market expectation. Right now: VIX term structure just flipped bullish (returned to contango) this week. Generally supportive for long options strategies that need time to play out.

**2. HY Credit Spreads (FRED: BAMLH0A0HYM2)**
Credit leads equities. When HY spreads widen, leverage unwinds, equities follow 4–6 weeks later. Tight spreads = less likely to see a sudden macro dislocation. Right now: near multi-year lows. Good backdrop for neutral-to-bullish positioning.

**3. Insider Cluster Detection**
When 2+ insiders from the same company buy within 21 days, the signal scores bullish. When they're selling in clusters — especially in a specific sector — I'm cautious about directional long calls in that sector. The platform flags these clusters automatically.

**Current signal picture (July 7, 2026):**
13 bullish / 8 bearish / 26 neutral. Macro regime: MIXED SIGNALS. Not full-risk-on but not a red flag backdrop either.

All of this is free without an account. The Short Squeeze Radar and Congress Tracker are also free and useful for avoiding landmines on specific names.

unstructuredalpha.com

---

### REPOST SCHEDULE (existing posts from REDDIT_POSTS.md + SOCIAL_MEDIA_BATCH_2.md)

| Post | Subreddit | When to Repost | Notes |
|------|-----------|----------------|-------|
| Post 1 (algotrading — Bonferroni methodology) | r/algotrading | After 2 weeks of karma-building comments | First attempt removed for new account. Comment on 5+ posts first. |
| Post 2 (r/SideProject builder story) | r/startups | Cross-post 7 days after Post 13 above | Different enough angle to stand alone |
| Post 4 (r/stocks data snapshot) | r/stocks | Monday July 14 morning — update signal counts first | Refresh the numbers from Today's Brief before posting |
| Post 6 (Batch 2 r/stocks) | r/stocks | Don't repost — refresh Post 4 instead | Same sub, too close together |
| Post 5 (r/quant Bonferroni) | r/quant | After r/algotrading gets traction, cross-post | Allowed, expands reach |

---

### THREADS TO COMMENT ON (search for these right now on Reddit)

Search Reddit for these threads and drop a comment that adds value first, then mention the tool if it's genuinely relevant:

**r/algotrading:**
- Search: "alternative data" — comment on anything about SEC filings, insider data, credit signals
- Search: "multiple testing" OR "Bonferroni" — natural opener to mention the lag-scan validation
- Search: "out of sample" — great fit for discussing OOS methodology

**r/stocks:**
- Any "what signals do you watch?" weekly thread — mention HY credit spreads + insider clusters
- "daily discussion" threads with macro questions — reference specific signal data (yield curve, VIX term structure)

**r/investing:**
- Yield curve threads — the re-steepen to +31bps is a natural topic right now
- Recession signal discussion threads — great fit for sharing what held up OOS

**r/thetagang:**
- "What's your macro read this week?" type threads — VIX term structure flip is timely
- Any thread about "how do you decide when to sell premium" — the confluence score use case fits perfectly

**Comment template (customize per thread):**
> [Answer their question substantively first — 2–3 sentences of real value]
>
> I actually built a dashboard around this — [specific feature relevant to thread]. It's at unstructuredalpha.com, most pages are free. [One specific data point from the signal dashboard relevant to the conversation.]

---

## PART 3: NEW TWITTER/X POSTS

**Account: @UnstAlpha**
**Current post count: 1 (Jul 6 launch post)**
**Goal: Get to 15+ posts this week, 2/day pace**
**Post times: 8–10am ET on weekdays, 11am–1pm ET on weekends**

---

### TWEET 1 — Standalone hook (post TODAY, Jul 7)
> The yield curve just turned positive for the first time since 2022.
>
> 10Y: 4.38% | 2Y: 4.07% | Spread: +31bps
>
> Historically, re-steepening after long inversions is LATE-cycle, not early-cycle. The recession often comes *after* the curve goes positive.
>
> The question isn't whether to be bullish. It's whether you're in the right part of the cycle.

---

### TWEET 2 — Counter-intuitive take (Jul 7 or 8)
> Short interest alone is one of the worst signals I've tested.
>
> Across 40+ tickers, OOS: not consistently predictive of forward returns.
>
> Short interest + macro regime + insider cluster detection? That combination actually holds up.
>
> Context changes everything. Single signals are usually just noise dressed up as insight.

---

### TWEET 3 — Data snapshot (Jul 8, update numbers from live site first)
> Macro picture right now (Jul 7, 2026):
>
> 🟢 13 signals BULLISH
> 🔴 8 signals BEARISH
> ⚪ 26 signals NEUTRAL
>
> VIX term structure just flipped bullish.
> EIA crude draws: 7 consecutive weeks.
> HY credit spreads: near multi-year lows.
>
> Regime: MIXED but leaning constructive.
>
> Full read → unstructuredalpha.com/Today_Digest

---

### TWEET 4 — Thread on how insider clusters work (Jul 8 or 9, post as thread)

**Tweet 4a:**
> The strongest signal I've found in 6 months of testing: insider buying clusters.
>
> Not a single insider. Not a big insider. Two or more executives from the *same company* buying within 21 days of each other.
>
> Here's why that specific combination matters: 🧵

**Tweet 4b:**
> A single insider buying could be anything — diversification, a preset 10b5-1 plan, a sign-on grant.
>
> Two or more insiders buying *at the same time* with their own money means they looked at each other's decisions and still bought.
>
> That coordination signal is rare. Which is also why it survives Bonferroni correction and OOS testing when single-insider signals don't.

**Tweet 4c:**
> The N-is-small problem: insider clusters only appear a handful of times per name per year.
>
> I handle this by pooling across tickers in the same sector — if the signal fires in 3 tech names simultaneously, that's a sector-level read, not 3 independent data points.
>
> It's still a limited signal. But when it appears, it's the one I weight most.

**Tweet 4d:**
> You can run this yourself on any ticker at unstructuredalpha.com/Ticker_Deep_Dive
>
> The Insider Cluster badge shows when 2+ insiders bought within 21 days. The Deep Correlation Scan shows whether insider activity has historically predicted forward returns for that specific name.
>
> Free without an account.

---

### TWEET 5 — Engagement/question format (Jul 9)
> What's the one non-price data series you'd keep if you could only watch one?
>
> Mine: HY credit spreads (FRED: BAMLH0A0HYM2)
>
> Leads equity drawdowns by 4–6 weeks, it's free, and it doesn't lie.
>
> Drop yours below. Curious what this corner of FinTwit actually watches.

---

### TWEET 6 — The honest transparency angle (Jul 9 or 10)
> Every "alternative data" platform I've seen buries the failures.
>
> I publish mine:
>
> ❌ Social sentiment (Google Trends, StockTwits): failed OOS on every test
> ❌ Single commodity signals: beautiful in-sample, useless OOS
> ❌ Short interest alone: not a reliable predictor
>
> The stuff that works is boring. The stuff that sounds exciting usually doesn't hold up.
>
> unstructuredalpha.com/Model_Validation

---

### TWEET 7 — Feature spotlight: Congress Tracker (Jul 10)
> Congress members legally have to disclose stock trades within 45 days under the STOCK Act.
>
> Most people watch individual trades. What I watch: *clusters.*
>
> 3+ members buying the same ticker within 45 days = a signal that something is known at the committee level.
>
> We track this. It's free. unstructuredalpha.com/Congress_Tracker

---

### TWEET 8 — Product comparison angle (Jul 10 or 11)
> Most stock research tools give you:
> - Price charts
> - EPS estimates
> - Analyst ratings
>
> All of these are based on information that's already in the price.
>
> I built something that looks at what's *not* in the price yet: credit spreads, energy inventories, insider clusters, yield curve slope.
>
> The lag matters. unstructuredalpha.com

---

### TWEET 9 — "Did you know" format (Jul 11)
> Did you know EIA crude inventory data leads energy stock moves by ~3–5 weeks?
>
> Not a surprise — if refiners are drawing down inventory, demand is there. Prices follow. Equity multiples follow prices.
>
> We've had 7 consecutive weekly draws on crude inventories through July.
>
> XOM, CVX, SLB are the energy names where this signal has historically been most predictive in the lag scan.

---

### TWEET 10 — Short Squeeze Radar spotlight (Jul 11 or 12)
> How we score squeeze probability:
>
> 1. FINRA short interest % of float
> 2. Macro confluence score (is the broader environment supportive?)
> 3. Insider cluster signal (are insiders buying while shorts are piling in?)
>
> All three together → Short Squeeze Radar score (0–100)
>
> Single short interest screens miss #2 and #3. That's where most squeeze calls go wrong.
>
> Free: unstructuredalpha.com/Short_Squeeze_Radar

---

### TWEET 11 — Builder story (Jul 12)
> 6 months ago I started tracking macro signals in a spreadsheet.
>
> It became a Streamlit app. Then a full platform. Now: 47 signals, 28 pages, PostgreSQL backend, paying users.
>
> The thing I didn't expect: the hardest part wasn't the data engineering. It was figuring out which correlations were real and being honest enough to publish the ones that weren't.
>
> unstructuredalpha.com

---

### TWEET 12 — Educational: what HY spreads actually measure (Jul 12 or 13)
> Quick primer on why I track HY credit spreads (FRED: BAMLH0A0HYM2):
>
> When high-yield borrowers have to pay more to borrow → leverage is getting more expensive → leveraged buybacks and acquisitions slow → equity multiples compress.
>
> The spread usually widens *before* equities roll over. That's the lag that makes it useful.
>
> Right now: near multi-year lows. No credit stress signal.

---

### TWEET 13 — Engagement: poll format (Jul 13)
> When you're researching a stock, what do you check first?
>
> 🔵 Price/chart action
> 🟢 Fundamentals (EPS, revenue)
> 🟡 News & analyst ratings
> 🟤 Macro/sector backdrop
>
> (I'm building for the last one and curious how niche I am)

---

### TWEET 14 — Teaser for Weekly Brief (post Sunday Jul 13)
> Every Sunday I publish an AI-generated macro research note at unstructuredalpha.com/Weekly_Brief
>
> It's written from live signal state — not from generic market commentary.
>
> This week: yield curve re-steepen thesis, VIX term structure flip, what 7 consecutive crude draws mean for energy equities.
>
> Worth 5 minutes. Free.

---

## POSTING SCHEDULE OVERVIEW

| Date | Platform | Content |
|------|----------|---------|
| Mon Jul 7 | Reddit | Reply to both r/SideProject comments |
| Mon Jul 7 | Twitter | Tweet 1 (yield curve re-steepen) |
| Tue Jul 8 | Twitter | Tweet 2 (short interest myth-bust) |
| Tue Jul 8 | Reddit | Post r/stocks Post 6 (from Batch 2) 8–10am ET |
| Wed Jul 9 | Twitter | Tweet 3 (data snapshot) + Tweet 4 thread |
| Wed Jul 9 | Reddit | Comment on r/algotrading threads |
| Thu Jul 10 | Twitter | Tweet 5 (engagement question) + Tweet 6 (transparency) |
| Thu Jul 10 | Reddit | Comment on r/thetagang + r/investing threads |
| Fri Jul 11 | Twitter | Tweet 7 (Congress Tracker) + Tweet 8 (comparison) |
| Sat Jul 12 | Twitter | Tweet 9 (EIA data) + Tweet 10 (Short Squeeze) |
| Sun Jul 13 | Twitter | Tweet 11 (builder story) + Tweet 14 (Weekly Brief) |
| Mon Jul 14 | Twitter | Tweet 12 (HY spreads primer) |
| Mon Jul 14 | Reddit | Post 9 (r/SecurityAnalysis) |
| Tue Jul 15 | Twitter | Tweet 13 (poll) |
| Tue Jul 15 | Reddit | Post 10 (r/thetagang) |
| Wed Jul 16 | Reddit | Post 11 (r/MacroEconomics) |
| Thu Jul 17 | Reddit | Post 12 (r/Python) |
| Fri Jul 18 | Reddit | Post 13 (r/startups) |
| Mon Jul 21 | Reddit | Post 14 (r/options) |
| Mon Jul 21 | Reddit | Repost Post 1 to r/algotrading (after karma building) |

---

## TWITTER ENGAGEMENT RULES

- Reply to anyone who comments within 1 hour. Even a single "good point" reply boosts distribution.
- Retweet @UnstAlpha's own thread tweets from your personal account if you have one — it seeds early engagement.
- Quote-tweet Tweet 3 (data snapshot) every Monday with updated signal counts — this trains the algorithm to treat it as recurring content.
- On Tweet 5 (the question) — reply to EVERY answer with a substantive follow-up. That thread becoming active is the distribution mechanism.
- Don't reply to yourself publicly unless you're adding a thread continuation. Looks spammy.

## REDDIT ENGAGEMENT RULES

- Reply to every comment within the first hour of posting. Reddit algorithm weights early comment velocity.
- When you get a skeptical comment — engage genuinely. Don't be defensive. Skepticism that gets a thoughtful answer converts more readers than unchallenged praise.
- Upvote the comments on your own posts (you can't upvote your own post but you can upvote replies).
- After 50+ upvotes on a post: post a follow-up comment with a specific example (a signal that called something that played out, with dates and numbers).

---

## SUBREDDITS STILL UNTAPPED (for future batches)

- r/EconomicIndicators — very niche but perfect fit
- r/Wallstreetbets — only post if you have a specific short squeeze play to highlight; data-first framing required
- r/financialindependence — "macro context for DCA timing" angle
- r/Bogleheads — careful framing needed (they hate timing); "understanding the macro backdrop" not "timing the market"
- r/datascience — Python + ML methodology angle
- r/learnmachinelearning — the Bonferroni/OOS testing methodology post
- r/CFA — professional audience, loves rigor and methodology discussion
