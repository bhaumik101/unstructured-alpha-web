import { NextRequest, NextResponse } from "next/server";

// Simple email validation
function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const email = (body?.email || "").trim().toLowerCase();

    if (!email || !isValidEmail(email)) {
      return NextResponse.json({ error: "Invalid email" }, { status: 400 });
    }

    // ── Option A: Resend Contacts (set RESEND_API_KEY + RESEND_AUDIENCE_ID) ──
    const resendKey      = process.env.RESEND_API_KEY;
    const resendAudience = process.env.RESEND_AUDIENCE_ID;

    if (resendKey && resendAudience) {
      const res = await fetch(
        `https://api.resend.com/audiences/${resendAudience}/contacts`,
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${resendKey}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email, unsubscribed: false }),
        }
      );
      if (!res.ok) {
        const err = await res.text();
        console.error("[subscribe] Resend error:", err);
        // Don't block — fall through to console log
      } else {
        console.log(`[subscribe] Added ${email} to Resend audience ${resendAudience}`);
        return NextResponse.json({ success: true });
      }
    }

    // ── Option B: Log to stdout (always runs as fallback) ──
    console.log(`[subscribe] New subscriber: ${email} | ${new Date().toISOString()}`);
    return NextResponse.json({ success: true });

  } catch (err) {
    console.error("[subscribe] Error:", err);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
