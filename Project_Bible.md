# Unstructured Alpha — Project Bible

> **Unstructured Alpha** (n.) — In quantitative finance, "alpha" is excess return above a benchmark. "Unstructured" refers to non-traditional, non-financial data — satellite imagery, social sentiment, logistics data, supply chain signals. Unstructured Alpha is the edge you find where others aren't looking.

---

## 1. The Business

### What It Is
A paid intelligence platform — delivered as a weekly newsletter with an interactive data dashboard — that synthesizes niche, publicly available alternative data signals into actionable investment insights for serious retail investors, small family offices, and self-directed traders.

### Why It's Different
Traditional retail finance content tells people *what happened*. Unstructured Alpha tells people *what's coming* — using the same class of signals that hedge funds pay millions for, sourced from public data that nobody's packaging for a non-institutional audience.

### Target Audience
- **Primary:** Self-directed retail investors with $50K–$500K invested, ages 25–45, who read Bloomberg, follow macro Twitter, and are frustrated by surface-level analysis
- **Secondary:** Small RIAs and family offices that want supplemental signal coverage without paying Bloomberg Terminal prices
- **Tertiary:** Finance students and aspiring analysts who want to learn how professionals actually think

### Brand Voice
Institutional rigor, accessible language. No hype. No price targets. No "this is not financial advice" boilerplate buried in the footer — *lead* with the caveats and then deliver genuine analytical value. Think: a really smart friend who works at a hedge fund and actually explains their reasoning.

---

## 2. The Signal Library

### Tier Classification
- **Tier 1 — High Confidence:** Empirically validated with documented predictive cases. Lead with these.
- **Tier 2 — Supporting:** Strong theoretical basis + some empirical support. Use as confirmation signals.
- **Tier 3 — Exploratory:** Promising but limited track record. Flag as experimental.

### Predictive Confidence Score (PCS)
Rated 1–10 based on: (1) number of documented predictive instances, (2) causal mechanism clarity, (3) signal lead time, (4) data reliability. A PCS of 8+ is publication-grade. Below 6 gets disclosed as experimental.

---

### TIER 1 SIGNALS

#### 1. AAR Weekly Rail Traffic
**PCS: 9/10**
**Source:** Association of American Railroads (aar.org, free, weekly)
**What it measures:** Volume of freight moved by rail across 7 commodity categories — coal, grain, chemicals, autos, intermodal containers, petroleum, metals
**Causal mechanism:** Rail is how America moves physical goods. A drop in carload volume precedes inventory drawdowns and manufacturing slowdowns by 4–8 weeks. An acceleration in intermodal (container) volume signals import demand before it shows up in trade statistics.
**Documented cases:**
- The Atlanta Fed's GDPNow model formally incorporates rail traffic as a real-time GDP input
- Rail carloads dropped 8% YoY in Q4 2007, two quarters before the NBER officially declared the recession
- Auto loadings collapsed 34% in Jan–Feb 2020 before automaker earnings reflected COVID demand destruction
**How to use it:** Track week-over-week and year-over-year changes by commodity type. Divergences (e.g., grain up while chemicals down) tell you which sectors are accelerating vs. contracting.

---

#### 2. ATA Trucking Tonnage Index
**PCS: 9/10**
**Source:** American Trucking Associations (trucking.org, free, monthly)
**What it measures:** Weight of freight moved by US trucking — covers ~70% of all domestic freight
**Causal mechanism:** Trucks move almost everything that rails don't. The ATA index is a direct proxy for consumer and industrial demand. It's formally included in the Conference Board's Leading Economic Indicators.
**Documented cases:**
- ATA tonnage peaked in March 2018, 14 months before the manufacturing ISM entered contraction territory in August 2019
- The index fell 5.7% in February 2020 — the first month of COVID disruption — before any official economic data reflected the downturn
**How to use it:** Best used in combination with rail. When both drop simultaneously, it's a macro warning sign. When they diverge, it tells you about modal shift or sector-specific dynamics.

---

#### 3. WARN Act Filings
**PCS: 9/10**
**Source:** Department of Labor (dol.gov) + state labor department websites (free, ongoing)
**What it measures:** Legally required 60-day advance notice that companies must file before mass layoffs (50+ employees) or plant closings
**Causal mechanism:** Companies legally cannot hide large layoffs. WARN filings are a 60-day leading indicator of reported unemployment data — they appear before the Bureau of Labor Statistics ever sees the numbers.
**Documented cases:**
- Sears filed WARN notices in October 2018 for its store closure wave — investors who tracked the filings had 60 days of lead time before the bankruptcy announcement
- WARN filings in retail spiked 3x in January 2020, a full 60 days before COVID-related jobless claims hit record highs
- Circuit City's WARN filing wave in late 2008 telegraphed its bankruptcy filing months ahead
**How to use it:** Scrape or manually check state DOL WARN databases weekly. Cross-reference with retail, restaurant, and manufacturing sectors. A sudden spike in a specific industry is a sector-level short signal.

---

#### 4. USDA Crop Progress Reports
**PCS: 8/10**
**Source:** USDA National Agricultural Statistics Service (nass.usda.gov, free, weekly during growing season)
**What it measures:** Week-by-week planting progress, crop condition ratings (Excellent/Good/Fair/Poor/Very Poor), and harvest progress across all major US crops
**Causal mechanism:** Agricultural futures (corn, soybeans, wheat) price in crop condition weeks before USDA supply/demand reports. A deteriorating "Good + Excellent" percentage is a leading indicator of reduced supply and higher food costs, which flows through to grocery chains, food manufacturers, and restaurant margins.
**Documented cases:**
- The 2012 corn drought: Crop condition ratings fell from 60% G/E to 40% G/E over 8 weeks in June–July. Corn futures rose 45% in that period. Investors who tracked weekly ratings caught the move early.
- The 2019 Midwest flooding: Planting progress was 30% below the 5-year average by late May. Soybean futures priced in the supply disruption 6 weeks before USDA's June WASDE report confirmed it.
**How to use it:** Track the % rated Good + Excellent for corn, soybeans, and winter wheat. A 10+ percentage point decline from the 5-year average is meaningful. Layer against futures positioning data (CFTC Commitments of Traders) to see if the market has already priced it in.

---

#### 5. USDA Cold Storage Reports
**PCS: 8/10**
**Source:** USDA National Agricultural Statistics Service (nass.usda.gov, free, monthly)
**What it measures:** Inventory levels of frozen meat, poultry, dairy, and eggs held in commercial cold storage
**Causal mechanism:** Cold storage inventory is a direct supply/demand balancing mechanism for perishable proteins. Abnormally high inventory signals oversupply and coming price pressure; abnormally low signals potential price spikes. Processors build or draw down inventory based on demand expectations they have from buyers — making it a 6–8 week leading indicator of retail protein prices.
**Documented cases:**
- Chicken wing cold storage inventories hit record lows in early 2021 as restaurant reopening demand surged. Wing prices at food service spiked 70%+ that summer. Wingstop and Buffalo Wild Wings both cited it in earnings calls — but cold storage data showed it coming months earlier.
- Pork belly cold storage (the basis for bacon prices) fell to 20-year lows in 2016. Bacon prices spiked 12% that quarter. Grocery chains with high breakfast food exposure took a margin hit.
**How to use it:** Track monthly changes in chicken, beef, and pork cold storage vs. 5-year averages. This is the most niche signal in the library — almost nobody in retail finance tracks it.

---

#### 6. EPA Fuel Purchases (Weekly Petroleum Status Report)
**PCS: 8/10**
**Source:** US Energy Information Administration (eia.gov, free, weekly)
**What it measures:** US crude oil inventory levels, refinery utilization, gasoline demand (implied from product supplied), and distillate stocks
**Causal mechanism:** Gasoline demand is directly correlated with economic activity. Rising implied demand = people driving more = employment and consumer confidence improving. Refinery utilization indicates industrial demand for fuel.
**Documented cases:**
- Gasoline demand (4-week moving average) fell off a cliff in March 2020 — two weeks before stay-at-home orders were broadly announced
- Distillate (diesel) demand is a trucking proxy — it fell 15% in Q4 2008, ahead of the official GDP contraction
**How to use it:** Track the 4-week average implied gasoline demand YoY. Cross-reference with ATA trucking tonnage for confirmation of demand trends.

---

### TIER 2 SIGNALS

#### 7. LinkedIn Job Posting Velocity
**PCS: 7/10**
**Source:** LinkedIn (manual tracking or LinkedIn Talent Insights if you get access), Google Jobs scraping
**What it measures:** Rate of new job postings at specific companies or within specific industries over time
**Causal mechanism:** Hiring is a leading indicator of revenue expectations. Companies hire ahead of growth and freeze hiring ahead of contractions. Tracking job posting counts at major public companies gives you 60–90 days of lead time on hiring intentions before they show up in earnings.
**How to use it:** Track weekly posting counts for a watchlist of 20–30 companies. A company that's posting 40% more software engineers than 90 days ago is signaling a growth phase. A company that's pulled all open reqs is signaling a freeze.

---

#### 8. Google Trends — Sector-Specific Queries
**PCS: 7/10**
**Source:** Google Trends (trends.google.com, free)
**What it measures:** Relative search volume for specific terms, indexed to 100
**Causal mechanism:** Search behavior precedes purchase behavior by 2–4 weeks. Surging searches for specific products, services, or financial topics often predict demand spikes before they appear in sales data.
**Documented cases:**
- Searches for "refinance mortgage" tracked 6–8 weeks ahead of actual refinancing application volumes (which the MBA reports weekly)
- "Unemployment benefits how to apply" searches in late February 2020 preceded the historic March 2020 jobless claims spike
**How to use it:** Track a basket of queries relevant to your coverage sector. Normalize for seasonality. A 2-standard-deviation move above the seasonal baseline is worth flagging.

---

#### 9. CFTC Commitments of Traders (COT)
**PCS: 7/10**
**Source:** Commodity Futures Trading Commission (cftc.gov, free, weekly)
**What it measures:** Positioning of commercial hedgers, large speculators, and small speculators in futures markets across commodities, currencies, and financial contracts
**Causal mechanism:** Commercial hedgers (farmers, manufacturers, airlines) have real economic exposure — their positioning reflects actual business conditions. When commercials are heavily net long, they're hedging against rising prices they expect from real demand. Extreme speculator positioning in either direction is a contrarian indicator.
**How to use it:** Track net positions by category. Extreme speculator net longs (top decile historically) are often contrarian short setups. Commercial net longs at extremes often precede price increases.

---

### TIER 3 SIGNALS (Experimental)

#### 10. App Store Ranking Changes
**PCS: 6/10**
**Hypothesis:** Sustained moves in app store rankings for financial apps (Robinhood, Coinbase, banking apps) signal retail investor engagement before it shows up in platform metrics or user growth disclosures.

#### 11. OpenTable Reservation Volume
**PCS: 6/10**
**Hypothesis:** OpenTable publishes indexed reservation data by city. Sustained changes reflect consumer discretionary health with 3–4 week lead time on restaurant earnings.

#### 12. Vessel Tracking / Port Congestion Data
**PCS: 6/10**
**Hypothesis:** Public AIS vessel tracking data (MarineTraffic free tier) shows container ship wait times at major ports. Port congestion was a 6-month leading indicator of supply chain inflation in 2021.

---

## 3. Revenue Streams (Nine Total)

### Tier A — Core (Build First)

**1. Paid Newsletter Subscription**
$20/month or $180/year (10% discount). Target: 1,000 subscribers = $20K MRR. Use Substack or Ghost.

**2. Interactive Data Dashboard (Paywalled)**
Subscribers access a live dashboard showing all signals updated weekly. Built in Streamlit or Observable. Upgrades free subscribers to paid.

**3. Premium Tier — "Institutional Access"**
$99/month. Includes: full signal library access, raw data downloads (CSV), 1-page weekly signal summary PDF, early access to issues before public release. Target: 200 subscribers = $19.8K MRR.

### Tier B — Leverage (Build at 500 Subscribers)

**4. Advertiser Sponsorships**
At 2,000+ subscribers with strong open rates (40%+), trading platforms (Tastytrade, Interactive Brokers, Composer) will pay $500–2,000/issue for a single sponsor slot. Do not run more than one sponsor per issue.

**5. Affiliate Commissions**
Recommend data tools, brokerage accounts, and financial software with affiliate arrangements. Tastytrade: $100–200 per funded account. Seeking Alpha: $50–100 per subscription referral. Only recommend things you actually use.

**6. Signal Licensing to Small RIAs**
Package the signal library as a monthly data feed ($299–499/month per firm). Sell to RIAs with $50M–$500M AUM who want supplemental alternative data coverage without paying institutional data costs. 10 clients = $35K–50K/month.

### Tier C — Scale (Build at 2,000 Subscribers)

**7. Course: "How to Find and Use Alternative Data"**
One-time purchase at $197–297. Curriculum: where to find free alternative data, how to clean and normalize it, how to build a signal, how to backtest it, how to write about it. Sell to the finance student and aspiring analyst segment.

**8. Custom Research Reports (B2B)**
On-demand deep dives for hedge funds, family offices, or corporates. Price: $1,500–5,000 per report. This is consulting revenue — high margin, low volume. Requires a track record from the newsletter.

**9. Equity Stake / Acquisition**
Terminal outcome. At 5,000+ paying subscribers and a demonstrated track record of signal accuracy, this becomes a legitimate acquisition target for Bloomberg, Morningstar, Refinitiv, or a financial media company. The subscriber list + proprietary signal framework is the asset.

---

## 4. Execution Phases

### Phase 1 — Infrastructure + Launch (Weeks 1–4)
- Set up Substack or Ghost (Ghost preferred for long-term — you own your subscriber list)
- Register domain: unstructuredalpha.com (or .co)
- Set up free tier (public) and paid tier ($20/month)
- Publish Issue #1: Lead with WARN Act filings + ATA Trucking Tonnage as the featured signals
- Distribution: Post to r/investing, r/SecurityAnalysis, finance Twitter/X, LinkedIn, your personal network

### Phase 2 — Build the Data Layer (Months 2–4)
- Learn Python basics (Pandas, Requests, BeautifulSoup)
- Automate data collection: AAR, ATA, WARN, USDA crop reports
- Build a basic Streamlit dashboard showing signal trends
- Gate dashboard behind paid subscription

### Phase 3 — Monetize Beyond Subscriptions (Months 5–9)
- Launch sponsor slot once you hit 1,000+ subscribers
- Set up affiliate links
- Begin outreach to small RIAs for signal licensing

### Phase 4 — Productize (Month 10+)
- Build out the course
- Hire a part-time research assistant or editor
- Consider a podcast as a free acquisition channel (audio version of each weekly issue)

---

## 5. The Weekly Issue — Template

**Subject line formula:** `[Signal Name] + [What It's Saying] + [Why It Matters Now]`
Example: *"WARN Filings Are Spiking in Tech — What 60-Day Lead Time Tells Us"*

**Issue structure:**
1. **Signal of the Week** (400–600 words): One deep-dive signal with full methodology, data, chart, and investment implication
2. **Signal Dashboard Snapshot** (150 words): 3–4 sentence updates on all other Tier 1 signals — green/yellow/red status
3. **What the Commercials Are Doing** (150 words): COT positioning update on 2–3 relevant futures
4. **One Contrarian Read** (200 words): A data point that contradicts the consensus narrative
5. **Data Sources This Week** (links): Full transparency on where every number came from

Target length: 1,000–1,200 words. Readable in 8 minutes.

---

## 6. Legal & Compliance

- **Not a registered investment advisor.** Disclaim prominently. Do not issue price targets or specific buy/sell recommendations. Issue *signal interpretations*, not *investment advice*.
- **Data sourcing transparency.** Cite every source. If you scraped something, say so. Do not represent third-party data as proprietary.
- **No front-running.** Do not build positions in securities you plan to cover and then publish bullish coverage. This is securities fraud.
- **GDPR/CAN-SPAM.** Use a newsletter platform that handles unsubscribes and data privacy automatically (Ghost, Substack, Beehiiv all handle this).
- **Copyright.** You can summarize, analyze, and link to publicly available government data. Do not republish third-party paywalled data (Bloomberg, Refinitiv, etc.).

---

## 7. Power & Next-Gen Infrastructure Signal Library

> **The thesis:** AI, quantum computing, and the electrification of everything are creating a demand shock for power that the grid was never designed to handle. The companies, commodities, and infrastructure plays that win this cycle are telegraphed months to years in advance in public data that almost nobody is synthesizing for a retail audience. This is the most underserved signal category in financial media right now.

---

### NUCLEAR SIGNALS

#### N-1. NRC Construction Permit & License Applications
**PCS: 9/10**
**Source:** Nuclear Regulatory Commission (nrc.gov — ADAMS document search, free)
**What it measures:** Applications to build, operate, or extend the life of nuclear reactors in the US — including large light-water reactors, Small Modular Reactors (SMRs), and advanced non-light-water designs
**Causal mechanism:** NRC applications are a 3–7 year leading indicator of new nuclear capacity. The construction permit process is public record. Each application represents a committed capital decision — utilities and energy companies don't file unless they've secured financing and site agreements. The pipeline of applications tells you where nuclear capacity will exist in 2030–2035 before any earnings call or press release does.
**Current landscape (as of mid-2026):**
- TerraPower received the **first-ever NRC construction permit for a non-light-water reactor** (Natrium design) in March 2026 and broke ground in April 2026
- NuScale's US460 Unit 1 received NRC approval — the first next-generation advanced power reactor approved
- NRC finalized "Part 53" in April 2026 — the first new reactor licensing framework in decades, designed specifically to accelerate advanced reactor approvals
- DOE selected TVA and Holtec for $800M in SMR deployment funding; Palisades nuclear plant restart received a $1.52B DOE loan guarantee
- Dow/X-energy Xe-100 reactor construction permit application (Seadrift, TX) under active NRC review
**How to track:** Set up ADAMS email alerts at nrc.gov for new permit applications. Any new construction permit application = 3–5 year capital cycle signal. Subsequent license renewals = existing plant lifespan extension signal.
**Investment implications:** Uranium enrichers (Centrus), nuclear fuel fabricators, SMR developers (NuScale, X-energy), and utilities with nuclear exposure (Constellation, Vistra, Talen Energy) all move on NRC pipeline developments.

---

#### N-2. Uranium Spot Price + SWU Contract Rates
**PCS: 8/10**
**Source:** Tradetech (uranium.info — free weekly spot price), UxC (subscription, but weekly headlines are public), World Nuclear Association for SWU market context
**What it measures:**
- **Uranium spot price:** The current market price for U₃O₈ (yellowcake uranium) — the raw feedstock for nuclear fuel
- **SWU (Separative Work Unit) price:** The cost of uranium enrichment — converting natural uranium into enriched uranium fuel. This is the true bottleneck in the nuclear fuel supply chain.
**Causal mechanism:** Uranium and SWU prices are the input cost signal for nuclear energy economics. Rising prices signal that utilities are competing for scarce fuel supply — which only happens when they're building or extending reactors. Critically, **SWU is now the binding constraint** in Western nuclear fuel supply: the US has one enrichment plant (Urenco, 4.9M SWU/yr capacity) against ~15M SWU/yr of national requirements. Western enrichment capacity is ~8M SWU globally vs. 65M SWU worldwide — Russia's Rosatom dominates. This is a geopolitical signal embedded in a commodity price.
**Current data (mid-2026):**
- Uranium spot hit $99/lb in January 2026 — highest in 17 months
- SWU spot at ~$185/SWU; term contracts at ~$166/SWU
- Physical uranium funds (Sprott Uranium Trust) are accumulating spot supply, tightening the market further
**How to track:** Check uranium.info weekly. Track both the spot price AND the spread between spot and term contracts — a widening spread means utilities are rushing to lock in long-term supply (bullish signal for nuclear construction timeline). SWU prices above $175 spot are historically associated with accelerating reactor commitments.
**Investment implications:** Cameco (CCJ), Kazatomprom, Centrus Energy (LEU — the only US enricher), uranium royalty companies, and nuclear ETFs (URA, NLR).

---

#### N-3. DOE Loan Guarantee Program Pipeline (Title XVII)
**PCS: 8/10**
**Source:** Department of Energy Loan Programs Office (energy.gov/lpo, free — public solicitations and announcements)
**What it measures:** Federal loan guarantees and direct lending for nuclear energy projects, including SMRs, advanced reactors, and plant restarts
**Causal mechanism:** DOE loan guarantees de-risk the financing of projects that private capital alone won't fund. When DOE opens a solicitation, it's a policy signal that the administration is committing to a specific technology pathway. When projects receive conditional commitments, the capital cycle starts — suppliers, contractors, and fuel providers begin signing long-term agreements.
**Key signals to watch:**
- New solicitation announcements (signals policy intent, 6–18 months before project selection)
- Conditional commitments (signals project is moving to construction, 12–36 months before breaking ground)
- Financial close / first disbursement (construction starts, capital is flowing)
**Recent activity:** DOE issued a $900M SMR solicitation in March 2025. $800M awarded to TVA and Holtec in December 2025. $1.52B committed to Palisades restart. DOE targeting "criticality" for at least 3 demonstration reactors by July 4, 2026.
**How to track:** Subscribe to DOE LPO press releases at energy.gov/lpo. Also watch DOE's ARDP (Advanced Reactor Demonstration Program) announcements — 11 projects from 10 companies selected in 2025.

---

### GRID & POWER INFRASTRUCTURE SIGNALS

#### G-1. FERC Grid Interconnection Queue
**PCS: 9/10**
**Source:** FERC (ferc.gov — free), regional transmission organizations: PJM Interconnection, MISO, CAISO, SPP (all free, downloadable spreadsheets)
**What it measures:** All applications to connect new power generation or large loads to the transmission grid, pending FERC or RTO processing
**Causal mechanism:** The interconnection queue is the most forward-looking dataset in the US energy system. Projects in the queue represent committed capital — developers pay application fees and post financial deposits. The queue shows you where power generation will be built and where large new loads (data centers, factories) are planning to locate, 3–8 years before they go online.
**Current scale of the signal:**
- PJM has processed 170,000+ MW of new generation requests since 2023
- 30,000 MW remain in PJM's transition queue for 2026 processing
- PJM's December 2025 capacity auction fell 6,623 MW short of reliability targets — 5,100 MW of that shortfall driven by data center demand
- PJM's forecast peak load for 2027/28 is ~5,250 MW higher than the prior year's forecast
- FERC issued a December 2025 order creating a framework specifically for large co-located loads (data centers connecting directly to power plants, bypassing the normal grid)
**How to track:** Download the PJM, MISO, and CAISO interconnection queue spreadsheets monthly. Track: (1) total MW queued by fuel type; (2) "large load" interconnection applications — each one is a data center or manufacturer; (3) withdrawal rates — high withdrawal rates signal projects failing (bearish for that fuel type).
**Investment implications:** Utilities serving high-queue regions, transmission builders (Quanta Services, MYR Group, Primoris), transformer manufacturers (2–3 year order backlogs), and independent power producers.

---

#### G-2. Copper: LME Warehouse Stocks + COMEX Futures Spread
**PCS: 8/10**
**Source:** LME (lme.com — warehouse stock data, free daily), COMEX copper futures (CME Group), USGS Mineral Resources Program (free monthly)
**What it measures:** Physical copper supply and price — the single most important material input for grid buildout, data center construction, and electrification
**Causal mechanism:** Every megawatt of new power infrastructure requires copper — transmission lines, transformers, EV charging, solar inverters, and data center wiring. Grid modernization has now **overtaken EVs as copper's primary demand engine** (June 2026). AI data centers are projected to drive 400,000 tonnes of additional annual copper demand over the next decade, peaking around 572,000 tonnes in 2028. A structural supply deficit is projected starting in 2026 — the industry must bring on 900,000+ tonnes of new mine capacity per year to track demand, and current project pipelines can't deliver that.
**How to track:**
- LME copper warehouse stocks: When stocks fall below 200,000 tonnes, physical market is tight — price volatility increases
- COMEX front-month vs. 12-month futures spread: backwardation = physical tightness; contango = oversupply
- CFTC COT for copper: When managed money flips net short while commercials are net long, it's a contrarian long setup
**Investment implications:** Freeport-McMoRan (FCX), Teck Resources, copper royalty companies (Wheaton Precious Metals), COPX ETF. Indirectly: transformer manufacturers and wire/cable producers are capacity-constrained.

---

#### G-3. EIA Weekly Electric Power Data (STEO + Form EIA-923)
**PCS: 8/10**
**Source:** US Energy Information Administration (eia.gov — free, weekly/monthly)
**What it measures:** US electricity generation by fuel source, industrial power consumption, power plant capacity factors, and net generation additions
**Causal mechanism:** EIA data shows, in near-real-time, which fuel sources are providing power and at what utilization rates. For the AI/data center thesis, the key signal is the total US electricity demand growth rate. EIA projects 4,283 billion kWh in 2026 — tracking whether actual consumption is meeting or exceeding this forecast tells you whether the power demand bull thesis is playing out on schedule.
**Key metrics to track:**
- Total net electricity generation (month-over-month, year-over-year)
- Natural gas combined-cycle capacity factor (above 60% = tight market)
- Nuclear capacity factor (US nuclear typically runs 90%+ — any decline signals issues)
- Month-ahead power prices by region (PJM West Hub, ERCOT North, CAISO SP15) — forward price spikes = capacity tightness
**How to track:** eia.gov/electricity/data/browser — weekly updates. The Short-Term Energy Outlook (STEO) releases on the 15th of each month with power consumption forecasts.

---

### AI & DATA CENTER POWER DEMAND SIGNALS

#### A-1. Hyperscaler Capex vs. Utility Power Purchase Agreement Filings
**PCS: 8/10**
**Source:** SEC 10-K/10-Q filings (sec.gov — free), earnings call transcripts (Seeking Alpha free tier), state utility commission dockets (public, free, searchable by state)
**What it measures:** Capital expenditure commitments from Microsoft, Amazon, Google, and Meta for data center buildout — and the corresponding power procurement agreements they file with utilities
**Causal mechanism:** Hyperscaler capex is the cleanest demand signal for power infrastructure. When Microsoft announces $80B in data center capex and follows it with a power purchase agreement filed at a state utility commission, that's a multi-year, locked-in demand signal. The filing-to-delivery lag is 2–5 years — today's announcements forecast where power demand will be in 2027–2030.
**Current scale:** Data center electricity consumption surged 50% in 2025. AI-focused data centers are consuming electricity at 2.94x the rate of overall data center growth. US data center demand projected to hit 325–580 TWh by 2028, up from 176 TWh in 2023.
**How to track:** Pull hyperscaler 10-Q filings quarterly; search for "capital expenditures," "data center," and "power purchase agreement." Monitor state utility commission dockets for large PPAs — these are public filings that name the buyer.

---

#### A-2. Natural Gas Pipeline Permit Applications (FERC Docket)
**PCS: 8/10**
**Source:** FERC eLibrary (elibrary.ferc.gov — free, searchable)
**What it measures:** Applications to build, expand, or modify natural gas pipelines and compressor stations — the fuel delivery infrastructure for gas-fired power plants serving data centers
**Causal mechanism:** Natural gas is the fuel of choice for data center backup power and increasingly for base load (behind-the-meter gas turbines co-located with hyperscaler campuses). Data centers could add **6.1 Bcf/d** of US natural gas demand by 2030 — rivaling LNG export growth. Pipeline applications filed today become operational capacity in 2–4 years. A surge in permits in specific geographic corridors tells you where data center buildout is concentrated.
**Current regulatory shift:** FERC is overhauling its blanket certificate program for the first time since 2006 — increasing project cost limits and expanding what can be built without case-by-case approval. This accelerates the pipeline-to-construction timeline.
**How to track:** Search FERC eLibrary for CP (Certificate of Public Convenience) dockets. Filter for new pipeline construction applications. Map locations against known hyperscaler corridors: Northern Virginia/PJM, Texas/ERCOT, Phoenix metro.
**Investment implications:** Pipeline operators (Williams Companies, Kinder Morgan, Energy Transfer), gas-fired power developers, and utilities in data center corridors.

---

### QUANTUM COMPUTING INFRASTRUCTURE SIGNALS

#### Q-1. Peer-Reviewed Qubit Milestone Publications (arXiv Early Signal)
**PCS: 6/10 (Tier 2 — Emerging)**
**Source:** arXiv.org/list/quant-ph (free, daily preprints), IBM Quantum Blog, Google AI Blog, Nature/Science
**What it measures:** Technical progress in quantum computing hardware — qubit counts, error rates (gate fidelity), coherence times, and whether hardware has crossed the "below-threshold" error correction barrier
**Causal mechanism:** Quantum computing follows a known technical roadmap where specific milestones unlock commercial viability. The signal isn't the press release — it's the peer-reviewed paper, which appears on arXiv 2–6 weeks before the press release. When Google published the Willow chip paper showing "below-threshold" error correction in 2024, institutional investors began rotating into quantum plays within weeks of the paper dropping.
**Current milestones (mid-2026):**
- IBM: 433-qubit Condor deployed; targeting 4,000+ qubits and fault-tolerant modules by 2027; IBM-Cisco partnership targeting networked distributed quantum infrastructure by 2030
- Google: 1,000-qubit Willow; achieved "below threshold" error correction — the first physical prerequisite for fault-tolerant quantum
- Microsoft: Topological qubit architecture — fundamentally different approach, potentially more stable; behind on qubit count but ahead on error-protection theory
- Atom Computing: 1,225-qubit neutral-atom machine
**The key signal to watch:** The moment any major lab announces "quantum advantage" on a commercially relevant problem (not a contrived benchmark), the equity rotation into pure-play quantum stocks will be rapid. Track arxiv.org/list/quant-ph daily for papers from Google Quantum AI, IBM Research, and Microsoft Station Q.
**Investment implications:** IonQ (IONQ), Rigetti (RGTI), D-Wave (QBTS), IBM, Microsoft Azure Quantum, and quantum ETFs (QTUM).

---

#### Q-2. Dilution Refrigerator Order Backlog (Oxford Instruments)
**PCS: 7/10**
**Source:** Oxford Instruments annual reports and earnings calls (LSE: OXIG — free), Bluefors industry presentations (private company)
**What it measures:** Order backlog for dilution refrigerators — the specialized cooling equipment that keeps superconducting quantum processors at near-absolute-zero temperatures (~15 millikelvin). Fewer than 5 companies worldwide make them.
**Causal mechanism:** You cannot build a superconducting quantum computer without a dilution refrigerator. Lead time is 12–24 months. Backlog at the handful of manufacturers is the physical constraint on how fast quantum computing can scale. A surge in dilution refrigerator orders is a 12–24 month leading indicator of quantum computing lab expansion — at universities, national labs, and commercial operators. Bluefors dominates with ~70% market share; Oxford Instruments (OXIG) is the only major publicly traded comp.
**How to track:** Read Oxford Instruments interim results and annual reports for dilution refrigerator segment commentary. LinkedIn hiring data for cryogenic engineers is a secondary signal — labs don't hire cryo engineers unless equipment is arriving.
**Why this is niche:** Almost no retail finance publication covers equipment supply chains for quantum computing. This is exactly the kind of signal Unstructured Alpha exists to surface.

---

### THEMATIC SYNTHESIS: The Power Supercycle Signal Stack

The thesis that ties all of these signals together:

> AI training → requires massive compute → compute requires power → power requires grid infrastructure → grid requires copper, transformers, and new dispatchable generation → nuclear and gas fill the gap → uranium and SWU prices rise → quantum computing emerges as the next compute paradigm → the cycle repeats at a higher amplitude.

**When multiple signals flash simultaneously, conviction multiplies:**

| Signal 1 | Signal 2 | Combined Read |
|-----------|-----------|---------------|
| FERC interconnection queue surge in specific region | Hyperscaler capex announcement for same geography | Data center buildout confirmed — utility stocks and IPPs in that region are 2–3 year plays |
| NRC construction permit application filed | Rising SWU spot prices | Nuclear fuel supply chain tightening ahead of new capacity — enrichers are the bottleneck |
| LME copper stocks falling | COMEX copper in backwardation | Physical tightness ahead of grid buildout — mining stocks are lagging the signal |
| arXiv paper on error correction from IBM or Google | Oxford Instruments cryogenics backlog expansion | Quantum scale-up is real — equity rotation is 6–18 months out |
| Natural gas pipeline permit surge in Virginia/Texas | FERC large-load interconnection filings in same geography | Data center power demand is locking in gas demand for 20+ years in those markets |

This synthesis is what separates Unstructured Alpha from every other retail finance newsletter. Anyone can watch uranium prices. Nobody is watching all five signals simultaneously and telling readers what the combination means.

---

*Signal library last updated: June 2026. All sources are publicly available and free unless noted.*
