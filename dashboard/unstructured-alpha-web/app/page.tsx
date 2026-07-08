'use client';

import { useState } from 'react';

const APP_URL = "https://app.unstructuredalpha.com";

// ─── Data ────────────────────────────────────────────────────────────────────

const STATS = [
  { value: "15+", label: "Macro signals" },
  { value: "38", label: "Data sources" },
  { value: "~2h", label: "Update cycle" },
  { value: "$0", label: "To get started" },
];

const SOURCES = ["FRED", "SEC EDGAR", "FINRA", "EIA", "Yahoo Finance", "CBOE"];

const PREVIEW_SIGNALS = [
  { name: "Fed Funds Spread",  score: 72, cat: "Macro" },
  { name: "Yield Curve Slope", score: 61, cat: "Macro" },
  { name: "Insider Buy Ratio", score: 78, cat: "Sentiment" },
  { name: "Short Interest",    score: 29, cat: "Sentiment" },
  { name: "HY Credit Spread",  score: 34, cat: "Credit" },
  { name: "Oil Inventory Δ",   score: 68, cat: "Energy" },
  { name: "Gold / SPX Ratio",  score: 55, cat: "Commodity" },
  { name: "FINRA Margin Debt", score: 41, cat: "Credit" },
];

const FEATURES = [
  { icon: "⚡", title: "Signal Dashboard",    accent: "#00d566", pro: false,
    body: "All 15+ macro signals in a single heatmap. Spot bullish and bearish clusters across macro, commodity, credit, energy, and sentiment categories at a glance." },
  { icon: "🔍", title: "Ticker Deep Dive",    accent: "#00c8e0", pro: false,
    body: "Enter any ticker and see its Confluence Score, sector-relevant signals, insider activity, factor exposure, and earnings track record — all in one page." },
  { icon: "📋", title: "Today's Digest",      accent: "#7c3aed", pro: false,
    body: "A daily macro briefing that tells you which signals moved, by how much, and what it means in plain English. No charts to interpret — just context." },
  { icon: "📈", title: "Score History",        accent: "#00d566", pro: true,
    body: "Track how Confluence Scores have evolved over time. See which macro regimes preceded past market moves, and where we are now relative to history." },
  { icon: "🏭", title: "Sector Percentiles",  accent: "#00c8e0", pro: true,
    body: "Rank all sectors by their current macro tailwinds. See which sectors are in the top quartile of macro support and which are in the bottom." },
  { icon: "🔔", title: "Watchlist Alerts",    accent: "#7c3aed", pro: true,
    body: "Get notified when a Confluence Score for a ticker you follow crosses key thresholds — before the signal becomes consensus." },
];

const FOR_WHO = [
  { icon: "📊", title: "Active stock pickers",
    body: "You already have a thesis. Unstructured Alpha tells you whether the macro environment supports or undermines it — before you size in." },
  { icon: "🏦", title: "Macro-aware investors",
    body: "You follow Fed policy, credit spreads, and energy markets. We aggregate all of it into one daily score so you don't have to." },
  { icon: "⚙️", title: "Systematic thinkers",
    body: "You want data, not opinions. Every signal is pulled from public APIs, scored against a 2-year history, and updated every ~2 hours." },
];

const FAQ_ITEMS = [
  { q: "Is this real data or synthetic?",
    a: "Real. Every signal pulls from live public APIs — FRED for macro data, SEC EDGAR for Form 4 insider filings, FINRA for short interest, EIA for energy inventories. Scores update approximately every 2 hours during market hours." },
  { q: "How is this different from a Bloomberg Terminal?",
    a: "Bloomberg costs ~$24,000/year and is built for institutions. Unstructured Alpha is $20/month and designed for individual active investors who want the same macro signal layer without the enterprise overhead or the learning curve." },
  { q: "What does 'Confluence Score' mean?",
    a: "It's a 0–100 composite that weights the macro signals most relevant to a ticker's sector. Above 65 = strong macro tailwind. Below 35 = macro headwind. It's not a price prediction — it's context for whether the macro environment supports or undermines your thesis." },
  { q: "Can I cancel anytime?",
    a: "Yes. No contracts, no commitments. Cancel from your account settings and you won't be charged again. The free tier stays free forever." },
  { q: "Do I need to know Python or finance to use this?",
    a: "No. The dashboard is built for investors, not engineers. Scores are percentile-based (0–100), the digest explains what changed each day in plain English, and the Ticker Deep Dive gives you everything for a single stock on one page." },
];

const FREE_FEATURES = [
  "Signal Dashboard (all 15+ signals)",
  "Today's Digest (last 3 days)",
  "Ticker Deep Dive (3 tickers)",
  "Confluence Score preview",
];
const FREE_LOCKED = [
  "Full digest history",
  "Unlimited ticker analysis",
  "Score history charts",
  "Sector percentile rankings",
];
const PRO_FEATURES = [
  "Everything in Free",
  "Unlimited ticker analysis",
  "Full digest history (90 days)",
  "Score history charts",
  "Sector percentile rankings",
  "Watchlist alerts",
  "Early access to new signals",
  "Priority support",
];

// ─── Helpers ─────────────────────────────────────────────────────────────────

function cellStyle(score: number): React.CSSProperties {
  if (score >= 65) return { background: "rgba(0,213,102,0.15)", color: "#00d566", border: "1px solid rgba(0,213,102,0.25)" };
  if (score <= 35) return { background: "rgba(255,68,68,0.1)",  color: "#ff6b6b", border: "1px solid rgba(255,68,68,0.2)" };
  return { background: "rgba(255,255,255,0.04)", color: "#8892aa", border: "1px solid rgba(255,255,255,0.07)" };
}

const T = {
  muted:   "#8892aa" as const,
  dimmer:  "#4a5280" as const,
  label:   "#6b7fbb" as const,
  bright:  "#e8eaf2" as const,
  green:   "#00d566" as const,
  cyan:    "#00c8e0" as const,
  purple:  "#7c3aed" as const,
  bg:      "#0b0d12" as const,
  card:    "#12151e" as const,
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function Home() {
  const [annual, setAnnual]   = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const proPrice = annual ? 16 : 20;

  return (
    <div style={{ minHeight: "100vh", background: T.bg, color: T.bright, fontFamily: "var(--font-geist), Inter, system-ui, sans-serif" }}>

      {/* ── Ambient glow ── */}
      <div aria-hidden style={{ position: "fixed", top: 0, left: "50%", transform: "translateX(-50%)", width: 900, height: 500, background: "radial-gradient(ellipse at top, rgba(0,213,102,0.07) 0%, transparent 70%)", pointerEvents: "none", zIndex: 0 }} />

      {/* ─────────────────────────── NAV ─────────────────────────────────── */}
      <nav style={{ borderBottom: "1px solid rgba(255,255,255,0.06)", position: "sticky", top: 0, zIndex: 50, background: "rgba(11,13,18,0.9)", backdropFilter: "blur(12px)" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "0 24px", height: 60, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <a href="/" style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 700, fontSize: 15, letterSpacing: "-0.02em", color: T.bright, textDecoration: "none" }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.svg" alt="UA" style={{ width: 28, height: 28, flexShrink: 0, borderRadius: "50%" }} />
            Unstructured Alpha
          </a>
          <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
            <a href="#features" style={{ color: T.muted, fontSize: 14, textDecoration: "none" }}>Features</a>
            <a href="#pricing"  style={{ color: T.muted, fontSize: 14, textDecoration: "none" }}>Pricing</a>
            <a href="#faq"      style={{ color: T.muted, fontSize: 14, textDecoration: "none" }}>FAQ</a>
            <a href={APP_URL}   style={{ background: T.green, color: "#000", padding: "8px 18px", borderRadius: 8, fontSize: 14, fontWeight: 700, textDecoration: "none" }}>Launch App →</a>
          </div>
        </div>
      </nav>

      {/* ─────────────────────────── HERO ────────────────────────────────── */}
      <section style={{ maxWidth: 1100, margin: "0 auto", padding: "100px 24px 56px", textAlign: "center", position: "relative", zIndex: 1 }}>
        <div style={{ display: "inline-block", background: "rgba(0,213,102,0.1)", border: "1px solid rgba(0,213,102,0.3)", borderRadius: 100, padding: "4px 14px", fontSize: 12, color: T.green, fontWeight: 600, marginBottom: 28, letterSpacing: "0.04em", textTransform: "uppercase" }}>
          Early Access
        </div>
        <h1 style={{ fontSize: "clamp(38px, 5.5vw, 64px)", fontWeight: 800, lineHeight: 1.08, letterSpacing: "-0.04em", marginBottom: 24 }}>
          Macro signals.<br />
          <span style={{ background: "linear-gradient(90deg, #00d566 0%, #00c8e0 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            Before the move.
          </span>
        </h1>
        <p style={{ fontSize: 18, color: T.muted, maxWidth: 560, margin: "0 auto 44px", lineHeight: 1.75 }}>
          Insider flows, credit spreads, energy positioning, and Fed indicators — scored daily from public data and surfaced in one dashboard for active investors.
        </p>
        <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap", marginBottom: 52 }}>
          <a href={APP_URL} style={{ background: T.green, color: "#000", padding: "14px 32px", borderRadius: 10, fontSize: 15, fontWeight: 700, textDecoration: "none", display: "inline-block" }}>
            Start Free — No card needed
          </a>
          <a href="#features" style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: T.bright, padding: "14px 30px", borderRadius: 10, fontSize: 15, fontWeight: 600, textDecoration: "none", display: "inline-block" }}>
            See the Signals
          </a>
        </div>

        {/* Stat strip */}
        <div style={{ display: "flex", justifyContent: "center", flexWrap: "wrap", borderTop: "1px solid rgba(255,255,255,0.06)", borderBottom: "1px solid rgba(255,255,255,0.06)", padding: "20px 0" }}>
          {STATS.map((s, i) => (
            <div key={s.label} style={{ display: "flex", alignItems: "center", padding: "0 28px", borderRight: i < STATS.length - 1 ? "1px solid rgba(255,255,255,0.06)" : "none" }}>
              <div>
                <div style={{ fontSize: 22, fontWeight: 800, color: T.bright, letterSpacing: "-0.03em" }}>{s.value}</div>
                <div style={{ fontSize: 12, color: T.dimmer, marginTop: 2 }}>{s.label}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─────────────────── SOURCE TRUST STRIP ──────────────────────────── */}
      <div style={{ background: "rgba(255,255,255,0.02)", borderTop: "1px solid rgba(255,255,255,0.04)", borderBottom: "1px solid rgba(255,255,255,0.04)", padding: "14px 24px" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap", justifyContent: "center" }}>
          <span style={{ fontSize: 11, color: T.dimmer, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", flexShrink: 0 }}>Data from</span>
          {SOURCES.map((src) => (
            <span key={src} style={{ fontSize: 12, fontWeight: 600, color: T.label, background: "rgba(107,127,187,0.08)", border: "1px solid rgba(107,127,187,0.15)", borderRadius: 6, padding: "3px 10px", letterSpacing: "0.03em" }}>
              {src}
            </span>
          ))}
        </div>
      </div>

      {/* ─────────────────── SIGNAL PREVIEW ──────────────────────────────── */}
      <div style={{ background: "linear-gradient(180deg, rgba(0,213,102,0.04) 0%, transparent 100%)", borderTop: "1px solid rgba(0,213,102,0.15)", padding: "60px 24px" }}>
        <div style={{ maxWidth: 900, margin: "0 auto" }}>
          <p style={{ textAlign: "center", fontSize: 12, color: T.dimmer, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 24 }}>
            Live Signal Dashboard Preview
          </p>
          <div style={{ background: T.card, border: "1px solid rgba(255,255,255,0.07)", borderRadius: 16, padding: "24px", overflowX: "auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: T.bright }}>Macro Signal Scores</span>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 6, height: 6, borderRadius: "50%", background: T.green, boxShadow: `0 0 6px ${T.green}` }} />
                <span style={{ fontSize: 11, color: T.dimmer }}>Live · updated every ~2h</span>
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {PREVIEW_SIGNALS.map((sig) => (
                <div key={sig.name} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 14px", borderRadius: 8, background: "rgba(255,255,255,0.02)" }}>
                  <span style={{ fontSize: 10, fontWeight: 700, color: T.dimmer, letterSpacing: "0.08em", textTransform: "uppercase" as const, width: 72, flexShrink: 0 }}>{sig.cat}</span>
                  <span style={{ flex: 1, fontSize: 13, color: T.muted }}>{sig.name}</span>
                  <div style={{ width: 140, height: 4, background: "rgba(255,255,255,0.06)", borderRadius: 2, flexShrink: 0 }}>
                    <div style={{ width: `${sig.score}%`, height: "100%", borderRadius: 2, background: sig.score >= 65 ? T.green : sig.score <= 35 ? "#ff4444" : T.muted }} />
                  </div>
                  <span style={{ ...cellStyle(sig.score), borderRadius: 6, padding: "2px 10px", fontSize: 12, fontWeight: 700, flexShrink: 0, width: 40, textAlign: "center" as const }}>{sig.score}</span>
                </div>
              ))}
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 20, paddingTop: 16, borderTop: "1px solid rgba(255,255,255,0.05)", flexWrap: "wrap", gap: 12 }}>
              <div style={{ display: "flex", gap: 20 }}>
                {[{ label: "≥65 Bullish", color: T.green }, { label: "36–64 Neutral", color: T.muted }, { label: "≤35 Bearish", color: "#ff4444" }].map((l) => (
                  <div key={l.label} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: T.dimmer }}>
                    <div style={{ width: 8, height: 8, borderRadius: 2, background: l.color }} />{l.label}
                  </div>
                ))}
              </div>
              <a href={APP_URL} style={{ fontSize: 12, color: T.green, fontWeight: 600, textDecoration: "none" }}>View live dashboard →</a>
            </div>
          </div>
        </div>
      </div>

      {/* ─────────────────── HOW IT WORKS ────────────────────────────────── */}
      <div style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "80px 24px" }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: T.green, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 12 }}>How it works</p>
          <h2 style={{ fontSize: "clamp(24px, 3vw, 36px)", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 16 }}>From public data to actionable macro context</h2>
          <p style={{ fontSize: 16, color: T.muted, maxWidth: 520, lineHeight: 1.7, marginBottom: 56 }}>Three steps from raw filings and Fed data to a clear picture of the macro regime.</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 32 }}>
            {[
              { n: "01", title: "Signals scored daily",
                body: "We pull from FRED, SEC EDGAR, FINRA, EIA, and price feeds. Each signal gets a 0–100 percentile score against its 2-year history — so 72 means more bullish than 72% of recent readings." },
              { n: "02", title: "Confluence score per ticker",
                body: "For each ticker in your watchlist, we weight the signals relevant to its sector into a single Confluence Score. High = macro tailwind. Low = macro headwind. No guesswork." },
              { n: "03", title: "Daily digest explains the regime",
                body: "Every morning you get a plain-English summary of what changed and what it means — not just raw numbers, but actual context about what the macro environment is doing." },
            ].map((step) => (
              <div key={step.n} style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
                <div style={{ flexShrink: 0, width: 36, height: 36, background: "rgba(0,213,102,0.1)", border: "1px solid rgba(0,213,102,0.25)", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 700, color: T.green }}>{step.n}</div>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 6 }}>{step.title}</div>
                  <div style={{ fontSize: 14, color: T.muted, lineHeight: 1.65 }}>{step.body}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ─────────────────── FEATURES ────────────────────────────────────── */}
      <div id="features" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "80px 24px" }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: T.green, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 12 }}>Features</p>
          <h2 style={{ fontSize: "clamp(24px, 3vw, 36px)", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 16 }}>Everything in one place</h2>
          <p style={{ fontSize: 16, color: T.muted, maxWidth: 520, lineHeight: 1.7, marginBottom: 56 }}>No scattered tabs, no manual data hunting. One dashboard, all the macro context you need.</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 20 }}>
            {FEATURES.map((f) => (
              <div key={f.title} style={{ background: T.card, border: "1px solid rgba(255,255,255,0.07)", borderRadius: 14, padding: "28px", position: "relative" }}>
                {f.pro && (
                  <span style={{ position: "absolute", top: 16, right: 16, background: "rgba(124,58,237,0.15)", border: "1px solid rgba(124,58,237,0.3)", borderRadius: 6, fontSize: 10, fontWeight: 700, color: "#a78bfa", padding: "2px 8px", letterSpacing: "0.06em", textTransform: "uppercase" }}>Pro</span>
                )}
                <div style={{ fontSize: 28, marginBottom: 16 }}>{f.icon}</div>
                <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 10, letterSpacing: "-0.02em", background: `linear-gradient(90deg, ${T.bright}, ${f.accent})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", display: "inline-block" }}>{f.title}</div>
                <div style={{ fontSize: 14, color: T.muted, lineHeight: 1.7 }}>{f.body}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ─────────────────── WHO IT'S FOR ────────────────────────────────── */}
      <div style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", background: "rgba(255,255,255,0.01)" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "80px 24px" }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: T.green, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 12 }}>Built for</p>
          <h2 style={{ fontSize: "clamp(24px, 3vw, 36px)", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 56 }}>Active investors, not finance PhDs</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 20 }}>
            {FOR_WHO.map((w) => (
              <div key={w.title} style={{ background: T.card, border: "1px solid rgba(255,255,255,0.07)", borderRadius: 14, padding: "28px" }}>
                <div style={{ fontSize: 32, marginBottom: 16 }}>{w.icon}</div>
                <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 10, color: T.bright }}>{w.title}</div>
                <div style={{ fontSize: 14, color: T.muted, lineHeight: 1.7 }}>{w.body}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ─────────────────── PRICING ─────────────────────────────────────── */}
      <div id="pricing" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "80px 24px" }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: T.green, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 12, textAlign: "center" }}>Pricing</p>
          <h2 style={{ fontSize: "clamp(24px, 3vw, 36px)", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 16, textAlign: "center" }}>Start free. Go deeper with Pro.</h2>
          <p style={{ fontSize: 16, color: T.muted, maxWidth: 520, lineHeight: 1.7, textAlign: "center", margin: "0 auto 36px" }}>
            Free access gives you the signal dashboard and today&#39;s digest. Pro unlocks everything.
          </p>

          {/* Billing toggle */}
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 12, marginBottom: 48 }}>
            <span style={{ fontSize: 14, color: annual ? T.dimmer : T.bright, fontWeight: annual ? 400 : 600 }}>Monthly</span>
            <button
              onClick={() => setAnnual(!annual)}
              aria-label="Toggle annual billing"
              style={{ width: 44, height: 24, background: annual ? T.purple : "rgba(255,255,255,0.1)", borderRadius: 100, border: "none", cursor: "pointer", position: "relative", transition: "background 0.2s", flexShrink: 0 }}
            >
              <span style={{ position: "absolute", top: 2, left: annual ? 22 : 2, width: 20, height: 20, background: "#fff", borderRadius: "50%", transition: "left 0.2s", display: "block" }} />
            </button>
            <span style={{ fontSize: 14, color: annual ? T.bright : T.dimmer, fontWeight: annual ? 600 : 400 }}>Annual</span>
            {annual && (
              <span style={{ fontSize: 11, fontWeight: 700, color: T.green, background: "rgba(0,213,102,0.1)", border: "1px solid rgba(0,213,102,0.25)", borderRadius: 100, padding: "2px 8px" }}>Save 20%</span>
            )}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 20, maxWidth: 760, margin: "0 auto" }}>

            {/* Free */}
            <div style={{ background: T.card, border: "1px solid rgba(255,255,255,0.07)", borderRadius: 16, padding: "32px" }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: T.muted, letterSpacing: "0.1em", textTransform: "uppercase" as const, marginBottom: 12 }}>Free</div>
              <div style={{ fontSize: 42, fontWeight: 800, letterSpacing: "-0.04em", marginBottom: 4 }}>$0</div>
              <div style={{ fontSize: 13, color: T.dimmer, marginBottom: 28 }}>Forever free</div>
              <ul style={{ listStyle: "none", padding: 0, marginBottom: 28 }}>
                {FREE_FEATURES.map((f) => (
                  <li key={f} style={{ display: "flex", alignItems: "flex-start", gap: 10, fontSize: 14, color: T.muted, marginBottom: 12, lineHeight: 1.5 }}>
                    <span style={{ color: T.green, flexShrink: 0, marginTop: 1, fontSize: 13 }}>✓</span><span>{f}</span>
                  </li>
                ))}
                {FREE_LOCKED.map((f) => (
                  <li key={f} style={{ display: "flex", alignItems: "flex-start", gap: 10, fontSize: 14, color: T.dimmer, marginBottom: 12, lineHeight: 1.5 }}>
                    <span style={{ color: T.dimmer, flexShrink: 0, marginTop: 1, fontSize: 13 }}>—</span><span>{f}</span>
                  </li>
                ))}
              </ul>
              <a href={APP_URL} style={{ display: "block", textAlign: "center", padding: "12px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.12)", color: T.bright, fontSize: 14, fontWeight: 600, textDecoration: "none" }}>
                Get started free
              </a>
            </div>

            {/* Pro */}
            <div style={{ background: "rgba(124,58,237,0.08)", border: "1px solid rgba(124,58,237,0.4)", borderRadius: 16, padding: "32px", position: "relative" }}>
              <div style={{ position: "absolute", top: -12, left: "50%", transform: "translateX(-50%)", background: T.purple, color: "#fff", fontSize: 11, fontWeight: 700, padding: "3px 12px", borderRadius: 100, letterSpacing: "0.08em", textTransform: "uppercase" as const, whiteSpace: "nowrap" as const }}>
                Most popular
              </div>
              <div style={{ fontSize: 13, fontWeight: 700, color: T.muted, letterSpacing: "0.1em", textTransform: "uppercase" as const, marginBottom: 12 }}>Pro</div>
              <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 4 }}>
                <div style={{ fontSize: 42, fontWeight: 800, letterSpacing: "-0.04em" }}>${proPrice}</div>
                <span style={{ fontSize: 14, color: T.dimmer }}>/ month</span>
              </div>
              <div style={{ fontSize: 13, color: T.dimmer, marginBottom: 28 }}>
                {annual ? `Billed $${proPrice * 12}/year · cancel anytime` : "per month · cancel anytime"}
              </div>
              <ul style={{ listStyle: "none", padding: 0, marginBottom: 28 }}>
                {PRO_FEATURES.map((f) => (
                  <li key={f} style={{ display: "flex", alignItems: "flex-start", gap: 10, fontSize: 14, color: "#c4c9e0", marginBottom: 12, lineHeight: 1.5 }}>
                    <span style={{ color: T.purple, flexShrink: 0, marginTop: 1, fontSize: 13 }}>✓</span><span>{f}</span>
                  </li>
                ))}
              </ul>
              <a href={`${APP_URL}/Upgrade`} style={{ display: "block", textAlign: "center", padding: "12px", borderRadius: 10, background: T.purple, color: "#fff", fontSize: 14, fontWeight: 700, textDecoration: "none" }}>
                Upgrade to Pro ⚡
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* ─────────────────── FAQ ─────────────────────────────────────────── */}
      <div id="faq" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ maxWidth: 720, margin: "0 auto", padding: "80px 24px" }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: T.green, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 12, textAlign: "center" }}>FAQ</p>
          <h2 style={{ fontSize: "clamp(24px, 3vw, 36px)", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 52, textAlign: "center" }}>Common questions</h2>
          <div style={{ display: "flex", flexDirection: "column" }}>
            {FAQ_ITEMS.map((item, i) => (
              <div key={i} style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  style={{ width: "100%", textAlign: "left", padding: "20px 0", background: "none", border: "none", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}
                >
                  <span style={{ fontSize: 15, fontWeight: 600, color: T.bright }}>{item.q}</span>
                  <span style={{ color: T.dimmer, fontSize: 20, flexShrink: 0, lineHeight: 1, transform: openFaq === i ? "rotate(45deg)" : "none", transition: "transform 0.2s", display: "inline-block" }}>+</span>
                </button>
                {openFaq === i && (
                  <div style={{ paddingBottom: 20, fontSize: 14, color: T.muted, lineHeight: 1.75 }}>{item.a}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ─────────────────── CLOSING CTA ─────────────────────────────────── */}
      <div style={{ background: "linear-gradient(180deg, rgba(0,213,102,0.04) 0%, transparent 60%)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ maxWidth: 700, margin: "0 auto", padding: "100px 24px", textAlign: "center" }}>
          <h2 style={{ fontSize: "clamp(28px, 4vw, 48px)", fontWeight: 800, letterSpacing: "-0.04em", marginBottom: 20, lineHeight: 1.1 }}>
            See the macro signals<br />
            <span style={{ background: "linear-gradient(90deg, #00d566, #00c8e0)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              shaping your stocks.
            </span>
          </h2>
          <p style={{ fontSize: 17, color: T.muted, marginBottom: 40, lineHeight: 1.7, maxWidth: 460, margin: "0 auto 40px" }}>
            Free to start. No credit card. Takes 2 minutes to set up your watchlist.
          </p>
          <a href={APP_URL} style={{ background: T.green, color: "#000", padding: "16px 44px", borderRadius: 12, fontSize: 16, fontWeight: 800, textDecoration: "none", display: "inline-block", letterSpacing: "-0.01em" }}>
            Start Free →
          </a>
          <div style={{ marginTop: 20, fontSize: 13, color: T.dimmer }}>15+ live signals · Updated every ~2 hours · Cancel anytime</div>
        </div>
      </div>

      {/* ─────────────────── FOOTER ──────────────────────────────────────── */}
      <footer style={{ borderTop: "1px solid rgba(255,255,255,0.06)", padding: "48px 24px 32px" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 32, marginBottom: 40 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 700, fontSize: 15, letterSpacing: "-0.02em", color: T.bright, marginBottom: 10 }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/logo.svg" alt="UA" style={{ width: 28, height: 28, borderRadius: "50%" }} />
                Unstructured Alpha
              </div>
              <div style={{ fontSize: 13, color: T.dimmer, maxWidth: 300, lineHeight: 1.6 }}>
                Macro signal intelligence for active investors. Data sourced from FRED, SEC EDGAR, FINRA, EIA, and public price feeds.
              </div>
            </div>
            <div style={{ display: "flex", gap: 48, flexWrap: "wrap" }}>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: T.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 14 }}>Product</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <a href="#features" style={{ color: T.dimmer, fontSize: 13, textDecoration: "none" }}>Features</a>
                  <a href="#pricing"  style={{ color: T.dimmer, fontSize: 13, textDecoration: "none" }}>Pricing</a>
                  <a href={APP_URL}   style={{ color: T.dimmer, fontSize: 13, textDecoration: "none" }}>Launch App</a>
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: T.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 14 }}>Legal</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <a href={`${APP_URL}/36_Privacy_Policy`}    style={{ color: T.dimmer, fontSize: 13, textDecoration: "none" }}>Privacy Policy</a>
                  <a href={`${APP_URL}/37_Terms_of_Service`}  style={{ color: T.dimmer, fontSize: 13, textDecoration: "none" }}>Terms of Service</a>
                  <a href={`${APP_URL}/8_About`}              style={{ color: T.dimmer, fontSize: 13, textDecoration: "none" }}>About</a>
                </div>
              </div>
            </div>
          </div>
          <div style={{ borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: 24 }}>
            <p style={{ fontSize: 11, color: T.dimmer, lineHeight: 1.7, maxWidth: 800 }}>
              <strong style={{ color: T.label }}>Disclaimer:</strong> Unstructured Alpha is for educational and informational purposes only and does not constitute personalized financial, investment, tax, or legal advice. Nothing on this platform should be interpreted as a recommendation to buy, sell, or hold any security. Macro signals reflect statistical patterns in historical public data — they are not guarantees of future performance. Always consult a licensed financial adviser before making investment decisions.
            </p>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 16, flexWrap: "wrap", gap: 12 }}>
              <p style={{ fontSize: 12, color: T.dimmer }}>© {new Date().getFullYear()} Unstructured Alpha. All rights reserved.</p>
              <div style={{ display: "flex", gap: 24 }}>
                <a href={`${APP_URL}/36_Privacy_Policy`}   style={{ color: T.dimmer, fontSize: 13, textDecoration: "none" }}>Privacy</a>
                <a href={`${APP_URL}/37_Terms_of_Service`} style={{ color: T.dimmer, fontSize: 13, textDecoration: "none" }}>Terms</a>
              </div>
            </div>
          </div>
        </div>
      </footer>

    </div>
  );
}
