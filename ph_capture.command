#!/bin/bash
OUTDIR="/Users/bhaumikgiri/Documents/Claude/Projects/Unstructured Alpha Project/ph_screenshots"
mkdir -p "$OUTDIR"

nav_capture() {
    local url="$1" fname="$2"
    echo "→ Loading: $url"
    osascript << EOF
tell application "Google Chrome"
    activate
    set URL of active tab of front window to "$url"
end tell
EOF
    echo "  Waiting 12s for Streamlit..."
    sleep 12
    osascript -e 'tell application "Google Chrome" to activate'
    sleep 1
    WID=$(osascript -e 'tell application "System Events" to get id of first window of process "Google Chrome"' 2>/dev/null)
    if [ -n "$WID" ]; then
        screencapture -l "$WID" "$OUTDIR/$fname"
    else
        screencapture -x "$OUTDIR/$fname"
    fi
    echo "  Saved: $fname"
}

nav_capture "https://unstructuredalpha.com/Signal_Dashboard"      "ss1_signal_dashboard.png"
nav_capture "https://unstructuredalpha.com/Ticker_Deep_Dive"      "ss2_ticker_deep_dive.png"
nav_capture "https://unstructuredalpha.com/Model_Validation"      "ss3_model_validation.png"
nav_capture "https://unstructuredalpha.com/Short_Squeeze_Radar"   "ss4_short_squeeze.png"
nav_capture "https://unstructuredalpha.com/Today_s_Brief"         "ss5_today_brief.png"

echo ""
echo "✅ All 5 screenshots saved to:"
echo "   $OUTDIR"
echo ""
read -p "Press Enter to close..."
