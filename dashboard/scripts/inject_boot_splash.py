#!/usr/bin/env python3
"""
Build-time: inject a branded dark boot splash into Streamlit's served index.html.

WHY: Streamlit ships a single-page app whose ~MB JS bundle downloads BEFORE any of
our Python runs. During that window the browser shows a blank (dark, via our theme)
screen. Nothing in our app code can paint there — the only lever is the HTML page
Streamlit itself serves. This injects a full-viewport, on-brand loader (exact app
background #0B0D12, logo, animated bar) right after <body>, plus a self-removal
script with multiple hard timeouts so it can NEVER permanently cover the app.

SAFETY:
- Idempotent (skips if the marker is already present).
- Fully wrapped in try/except and ALWAYS exits 0 — a failure here must never fail
  the build or leave a half-written file (writes only after a successful transform).
- Trivially reversible: remove this step from render.yaml's buildCommand; the next
  deploy reinstalls a pristine Streamlit index.html.

Run from buildCommand AFTER `pip install`:  python scripts/inject_boot_splash.py
"""
import os
import re
import sys

MARKER = "ua-boot-splash"

SPLASH = """
<div id="ua-boot-splash" role="status" aria-label="Loading">
  <div class="ua-boot-inner">
    <div class="ua-boot-logo">UNSTRUCTURED <span>ALPHA</span></div>
    <div class="ua-boot-sub">Loading macro signal intelligence…</div>
    <div class="ua-boot-bar"><div class="ua-boot-bar-fill"></div></div>
  </div>
</div>
<style>
#ua-boot-splash{position:fixed;inset:0;z-index:2147483647;background:#0B0D12;
  display:flex;align-items:center;justify-content:center;
  transition:opacity .5s ease;
  font-family:'Inter','Segoe UI',system-ui,-apple-system,sans-serif;}
#ua-boot-splash.ua-hide{opacity:0;pointer-events:none;}
#ua-boot-splash .ua-boot-inner{text-align:center;}
#ua-boot-splash .ua-boot-logo{font-size:1.35rem;font-weight:800;letter-spacing:.04em;color:#E8EEFF;}
#ua-boot-splash .ua-boot-logo span{color:#00D566;}
#ua-boot-splash .ua-boot-sub{margin-top:8px;font-size:.72rem;color:#6B7FBF;letter-spacing:.02em;}
#ua-boot-splash .ua-boot-bar{margin:18px auto 0;width:180px;height:3px;border-radius:3px;
  background:rgba(255,255,255,.08);overflow:hidden;}
#ua-boot-splash .ua-boot-bar-fill{height:100%;width:40%;border-radius:3px;
  background:linear-gradient(90deg,#00D566,#7C3AED);
  animation:ua-boot-slide 1.1s infinite ease-in-out;}
@keyframes ua-boot-slide{0%{transform:translateX(-120%)}100%{transform:translateX(320%)}}
</style>
<script>
(function(){
  function hide(){
    var s=document.getElementById('ua-boot-splash');
    if(!s)return;
    s.classList.add('ua-hide');
    setTimeout(function(){if(s&&s.parentNode)s.parentNode.removeChild(s);},600);
  }
  function ready(){
    var app=document.querySelector('[data-testid="stAppViewContainer"]')
            ||document.querySelector('section.main')
            ||document.querySelector('.stApp');
    return !!(app && app.querySelector('[data-testid="stVerticalBlock"], .main, .block-container, section'));
  }
  var tries=0;
  var iv=setInterval(function(){tries++;if(ready()||tries>120){clearInterval(iv);hide();}},150);
  // Hard fallbacks — the splash must never persist.
  window.addEventListener('load',function(){setTimeout(hide,2500);});
  setTimeout(function(){clearInterval(iv);hide();},15000);
})();
</script>
"""


def main() -> None:
    try:
        import streamlit
        index_path = os.path.join(os.path.dirname(streamlit.__file__), "static", "index.html")
        if not os.path.isfile(index_path):
            print(f"[boot-splash] index.html not found at {index_path} — skipping", flush=True)
            return
        with open(index_path, "r", encoding="utf-8") as fh:
            html = fh.read()
        if MARKER in html:
            print("[boot-splash] already injected — skipping", flush=True)
            return
        new_html, n = re.subn(r"(<body[^>]*>)", r"\1" + SPLASH, html, count=1)
        if n != 1:
            print("[boot-splash] <body> tag not found — skipping (left untouched)", flush=True)
            return
        with open(index_path, "w", encoding="utf-8") as fh:
            fh.write(new_html)
        print(f"[boot-splash] injected branded splash into {index_path}", flush=True)
    except Exception as exc:  # never fail the build
        print(f"[boot-splash] skipped due to error: {exc}", flush=True)


if __name__ == "__main__":
    main()
    sys.exit(0)
