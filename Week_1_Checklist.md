# Unstructured Alpha — Week 1 Execution Checklist
**Goal: Publish Issue #1 by Sunday**

---

## Day 1 (Today) — Infrastructure Setup

### Platform
- [ ] Go to ghost.org — sign up for Creator plan ($9/month, 14-day free trial)
  - Alternative: Substack (free but Ghost gives you full list ownership)
- [ ] Set your publication name: **Unstructured Alpha**
- [ ] Set your tagline: *"The alternative data signals institutional investors actually use — for everyone else."*
- [ ] Set up two tiers:
  - Free: Access to 1 issue per month + signal dashboard teaser
  - Paid: $20/month or $180/year — full weekly access + dashboard

### Domain
- [ ] Register **unstructuredalpha.com** at Namecheap or Cloudflare (~$10/year)
  - Fallback if taken: unstructured-alpha.com or unstructuredalpha.co
- [ ] Connect custom domain to Ghost (takes 10 minutes, Ghost has a guide)

### Social
- [ ] Create **@UnstructuredAlpha** on X (Twitter) — this is your primary distribution channel
- [ ] Create matching LinkedIn page
- [ ] Write your bio: *"Alternative data signals for serious retail investors. Free signals weekly. No hype. No price targets."*

**End of Day Goal:** Platform live, domain connected, social accounts created.

---

## Day 2 — Pull Your Data

### Signal 1: WARN Act Filings (Lead Signal for Issue #1)
- [ ] Go to dol.gov/agencies/eta/layoffs/warn
- [ ] Download the most recent 60 days of federal WARN filings
- [ ] Also check your state's labor department WARN database (Google "[your state] WARN Act filings")
- [ ] Build a simple tally in Excel:
  - Companies filing in the last 30 days
  - Number of employees affected
  - Industry classification
  - Which states have the most activity
- [ ] Flag any clusters (multiple companies in same industry = sector signal)

### Signal 2: ATA Trucking Tonnage (Supporting Signal)
- [ ] Go to trucking.org/economics-and-industry-data
- [ ] Find the most recent Tonnage Index release (usually released mid-month for prior month)
- [ ] Note: current month vs. prior month, current month vs. same month last year
- [ ] Copy the key stat: "Trucking tonnage [rose/fell] X% in [month], [above/below] the X% YoY change in [prior month]"

### Signal 3: AAR Rail Traffic
- [ ] Go to aar.org/data/weekly-railroad-traffic
- [ ] Download the most recent weekly report (free, PDF or spreadsheet)
- [ ] Note total carloads YoY% and intermodal YoY%
- [ ] Flag any commodity categories with large divergences from the 52-week trend

### Signal 4: CFTC COT (if time allows)
- [ ] Go to cftc.gov/MarketReports/CommitmentsofTraders
- [ ] Download the most recent Disaggregated COT report (Friday release)
- [ ] Focus on: crude oil, corn, S&P 500 futures — note commercial vs. speculator net positions

**End of Day Goal:** Raw data collected for all 3–4 signals. You have numbers to write about.

---

## Day 3 — Write the Issue

### Issue #1 Title Options (pick one):
- *"What 60-Day Notice Tells You: WARN Filings and the Labor Market Signal Nobody Tracks"*
- *"The Truck Driver's Market: Why ATA Tonnage Just Flashed [Yellow/Red/Green]"*
- *"Reading the Freight: What Rail and Truck Data Are Saying About the Economy Right Now"*

### Issue Structure (copy this template):

---

**[Issue #1]**

*Signal of the Week: [Signal Name]*

[2–3 sentence hook — what's surprising or counterintuitive about what the data shows right now]

**What is [signal name]?**
[3–4 sentences explaining the signal to someone who's never heard of it. Explain why professionals pay attention to it.]

**What the data shows:**
[Current reading. Prior reading. Year-over-year change. Pull the exact numbers from your Day 2 research.]

**Why this matters:**
[Connect the data to real economic implications. What industry or stock could be affected? What would need to happen for this signal to confirm or reverse?]

**Historical context:**
[1–2 documented historical cases where this signal worked. Use specific dates and numbers. Examples: the 2012 corn drought, the Sears WARN filings, the 2020 trucking collapse.]

---

**Signal Dashboard Snapshot**

| Signal | Status | Reading | vs. Prior | vs. Last Year |
|--------|--------|---------|-----------|---------------|
| WARN Act Filings | 🟡 Elevated | [#] filings | [+/-X%] | [+/-X%] |
| ATA Trucking Tonnage | 🟢 Expanding | [index] | [+/-X%] | [+/-X%] |
| AAR Rail Carloads | 🟡 Mixed | [#] carloads | [+/-X%] | [+/-X%] |

*(Color coding: 🟢 = bullish signal, 🟡 = mixed/watch, 🔴 = bearish signal)*

---

**One Contrarian Read**

[Find one data point that contradicts the prevailing market narrative. Even 2–3 sentences is fine. This trains readers to look for asymmetric information.]

---

**Data Sources**
- WARN Act: dol.gov/agencies/eta/layoffs/warn, accessed [date]
- ATA Trucking Tonnage: trucking.org, [month] report
- AAR Rail Traffic: aar.org, week of [date]

*Unstructured Alpha is not a registered investment advisor. Everything here is signal interpretation for educational purposes, not investment advice. Do your own diligence.*

---

### Writing Tips for Issue #1:
- Aim for 900–1,100 words total
- Lead with the most surprising or actionable finding
- Use specific numbers, not vague language ("trucking tonnage fell 3.2%" not "trucking was weaker")
- End with a clear "what to watch" — what would make this signal more or less significant in the coming weeks

**End of Day Goal:** Draft complete.

---

## Day 4 — Edit and Prep Distribution

### Edit Pass:
- [ ] Read the draft aloud — anything that sounds like jargon, simplify it
- [ ] Check every number against your source data
- [ ] Make sure the signal dashboard table is filled in with real numbers
- [ ] Add 1–2 simple charts if you can (screenshot from the USDA/ATA website is fine for Issue #1)

### Pre-Launch Setup:
- [ ] Write your welcome email (goes to every new subscriber automatically):
  - 3 sentences: who you are, what Unstructured Alpha is, what to expect weekly
  - "Reply to this email — I read every one."
- [ ] Set up the paid subscription wall in Ghost
- [ ] Add your Stripe account to Ghost for payment processing (takes 10 minutes)

**End of Day Goal:** Edited draft ready. Ghost fully configured with payment processing.

---

## Day 5 — Launch

### Publish:
- [ ] Upload the issue to Ghost
- [ ] Set free tier to receive the intro + first two sections only
- [ ] Gate the Signal Dashboard, Contrarian Read, and Data Sources behind the paid tier
- [ ] Schedule for 7:00 AM your time (morning reads perform better)

### Distribution (do all of these on launch day):

**Reddit (highest volume, do this first):**
- [ ] Post to r/SecurityAnalysis: Write a genuine post summarizing your WARN finding. Link to the free version of the issue. Title format: "WARN Act filings just spiked in [sector] — 60-day leading indicator says [X]"
- [ ] Post to r/investing (same post, slightly shorter)
- [ ] Do NOT spam. One post per subreddit, genuine framing.

**X (Twitter):**
- [ ] Write a 4–5 tweet thread summarizing the key finding
  - Tweet 1: The surprising finding (hook)
  - Tweet 2: What the signal is and why it matters
  - Tweet 3: The historical case (e.g., Sears WARN filing)
  - Tweet 4: What you're watching next
  - Tweet 5: Link to the full issue + "subscribe for weekly signal updates"
- [ ] Tag 2–3 relevant finance accounts (don't beg for RTs, just relevant engagement)

**LinkedIn:**
- [ ] Post the thread as a LinkedIn article or post
- [ ] Finance content performs well on LinkedIn — use the same thread but expand to 300–400 words

**Your Personal Network:**
- [ ] Text or email 10 people personally who you think would find this genuinely useful
- [ ] Do not mass-email your contacts — personal messages convert 5–10x better
- [ ] Ask them to share it if they find it valuable, not to subscribe (the share does the work)

**Finance Discord/Slack Communities:**
- [ ] Find 2–3 active finance or investing Discord servers
- [ ] Post in their appropriate channels (usually #research or #macro)
- [ ] Engage with any replies — do not ghost your own launch

**End of Day Goal:** Issue published. Posted to Reddit, Twitter, LinkedIn. 10 personal messages sent.

---

## Days 6–7 — Monitor and Respond

- [ ] Reply to every comment on Reddit and Twitter
- [ ] Track subscriber count (Ghost dashboard) — set a goal: 25 subscribers in Week 1 is excellent
- [ ] Note which distribution channel drove the most signups (Ghost shows referral sources)
- [ ] Write a brief note on what you'd do differently for Issue #2
- [ ] Start pulling data for Issue #2 signal (suggestion: USDA Crop Progress if growing season, or Cold Storage Report)

---

## Week 1 Success Metrics

| Metric | Minimum | Good | Great |
|--------|---------|------|-------|
| Free subscribers | 15 | 50 | 100+ |
| Paid subscribers | 0 | 2 | 5+ |
| Open rate (free list) | 30% | 50% | 60%+ |
| Reddit upvotes (r/SecurityAnalysis) | 10 | 50 | 100+ |
| Twitter impressions | 500 | 2,000 | 5,000+ |

**The only metric that matters long-term is subscriber growth rate. Everything else is noise in Week 1.**

---

## Standing Weekly Workflow (Starting Week 2)

| Day | Task |
|-----|------|
| Monday | Pull all signal data (2 hours) |
| Tuesday | Write the issue draft (3 hours) |
| Wednesday | Edit + add charts (1 hour) |
| Thursday | Schedule for Friday 7AM release |
| Friday | Issue goes live. Run distribution. |
| Weekend | Engage with responses. Start thinking about next week's lead signal. |

---

*Next milestone after Week 1: 100 free subscribers. At 100, the feedback you get from engaged readers will be more valuable than anything you planned ahead of time.*
