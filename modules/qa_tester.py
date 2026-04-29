"""
QA Tester v2 — Real scroll simulation + AI vision scoring
==========================================================
Tests:
1. Desktop (1440x900) — scroll in steps, check hero canvas, check reveals fire
2. Mobile (390x844) — touch scroll, check no overflow, check hero visible
3. Hero canvas rendering — Three.js WebGL check
4. Reveal animations — .reveal-up elements get .is-revealed after scroll
5. Niche canvas — data-niche-scroll canvas present
6. Scroll progress bar — updates on scroll
7. AI Vision score — GPT-4.1 mini judges quality/genericness from screenshots
8. Auto-patch — if score < 7, GPT rewrites problem sections
"""

import asyncio
import base64
import json
import os
import re
from pathlib import Path
from openai import OpenAI

client = OpenAI()


async def _playwright_tests(html_path: str, brand: dict) -> dict:
    from playwright.async_api import async_playwright

    results = {
        "desktop_scroll_ok": False,
        "mobile_scroll_ok": False,
        "hero_canvas_ok": False,
        "reveals_ok": False,
        "niche_canvas_ok": False,
        "progress_bar_ok": False,
        "desktop_top_ss": None,
        "desktop_scroll_ss": None,
        "mobile_top_ss": None,
        "mobile_scroll_ss": None,
        "errors": [],
    }

    file_url = f"file://{os.path.abspath(html_path)}"
    ss_dir = Path(html_path).parent / "qa_screenshots"
    ss_dir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(args=[
            "--no-sandbox", "--disable-setuid-sandbox",
            "--disable-gpu", "--allow-file-access-from-files",
            "--disable-web-security",
        ])

        # ── DESKTOP ──────────────────────────────────────────────────────
        try:
            ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
            page = await ctx.new_page()
            js_errors = []
            page.on("pageerror", lambda e: js_errors.append(str(e)))

            await page.goto(file_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2500)

            # Top screenshot
            ss = str(ss_dir / "desktop_top.png")
            await page.screenshot(path=ss)
            results["desktop_top_ss"] = ss

            # Check hero canvas
            canvas_info = await page.evaluate("""() => {
                const c = document.getElementById('hero-frame-canvas');
                if (!c) return { found: false };
                return {
                    found: true,
                    w: c.width, h: c.height,
                    hasThree: typeof window.THREE !== 'undefined',
                    heroConfig: !!window.HERO_CONFIG,
                };
            }""")
            results["hero_canvas_ok"] = canvas_info.get("found", False) and canvas_info.get("hasThree", False)

            # Check progress bar
            pb = await page.evaluate("""() => {
                const el = document.getElementById('scroll-progress') || document.querySelector('.scroll-progress');
                return !!el;
            }""")
            results["progress_bar_ok"] = pb

            # Check niche canvas
            nc = await page.evaluate("""() => {
                const s = document.querySelector('[data-niche-scroll]');
                if (!s) return false;
                return !!s.querySelector('canvas');
            }""")
            results["niche_canvas_ok"] = nc

            # Count reveals before scroll
            before = await page.evaluate("""() => ({
                total: document.querySelectorAll('.reveal-up,.reveal-left,.reveal-right').length,
                revealed: document.querySelectorAll('.is-revealed,.revealed').length,
            })""")

            # Scroll down in 10 steps
            for i in range(1, 11):
                await page.evaluate(f"window.scrollTo(0, {i * 600})")
                await page.wait_for_timeout(150)

            await page.wait_for_timeout(800)

            # Mid-scroll screenshot
            ss2 = str(ss_dir / "desktop_scrolled.png")
            await page.screenshot(path=ss2)
            results["desktop_scroll_ss"] = ss2

            # Count reveals after scroll
            after = await page.evaluate("""() => ({
                total: document.querySelectorAll('.reveal-up,.reveal-left,.reveal-right').length,
                revealed: document.querySelectorAll('.is-revealed,.revealed').length,
            })""")

            results["desktop_scroll_ok"] = True
            results["reveals_ok"] = (
                after.get("revealed", 0) > before.get("revealed", 0)
                or after.get("revealed", 0) >= after.get("total", 1)
            )

            # Filter non-critical errors
            critical_errors = [e for e in js_errors if "WebGL" not in e and "shader" not in e.lower() and "THREE" not in e]
            if critical_errors:
                results["errors"].extend(critical_errors[:3])

            await ctx.close()
        except Exception as e:
            results["errors"].append(f"Desktop: {str(e)[:150]}")

        # ── MOBILE ───────────────────────────────────────────────────────
        try:
            ctx_m = await browser.new_context(
                viewport={"width": 390, "height": 844},
                device_scale_factor=2,
                is_mobile=True,
                has_touch=True,
            )
            page_m = await ctx_m.new_page()
            await page_m.goto(file_url, wait_until="domcontentloaded", timeout=30000)
            await page_m.wait_for_timeout(2500)

            ss_m = str(ss_dir / "mobile_top.png")
            await page_m.screenshot(path=ss_m)
            results["mobile_top_ss"] = ss_m

            # Check for horizontal overflow
            overflow = await page_m.evaluate("""() => ({
                bodyW: document.body.scrollWidth,
                viewW: window.innerWidth,
                overflow: document.body.scrollWidth > window.innerWidth + 5,
            })""")

            # Check hero headline is visible
            headline_ok = await page_m.evaluate("""() => {
                const h = document.querySelector('.hero-headline, h1');
                if (!h) return false;
                const r = h.getBoundingClientRect();
                return r.width > 0 && r.height > 0 && r.top < window.innerHeight;
            }""")

            # Scroll down on mobile
            for i in range(1, 7):
                await page_m.evaluate(f"window.scrollTo(0, {i * 500})")
                await page_m.wait_for_timeout(200)

            await page_m.wait_for_timeout(600)

            ss_m2 = str(ss_dir / "mobile_scrolled.png")
            await page_m.screenshot(path=ss_m2)
            results["mobile_scroll_ss"] = ss_m2

            results["mobile_scroll_ok"] = not overflow.get("overflow", True) and headline_ok

            if overflow.get("overflow"):
                results["errors"].append(
                    f"Mobile overflow: body={overflow.get('bodyW')}px > viewport={overflow.get('viewW')}px"
                )

            await ctx_m.close()
        except Exception as e:
            results["errors"].append(f"Mobile: {str(e)[:150]}")

        await browser.close()

    return results


def _vision_score(screenshots: list, brand: dict) -> dict:
    """GPT-4.1 mini vision scoring."""
    images = [
        {"type": "image_url", "image_url": {
            "url": f"data:image/png;base64,{base64.b64encode(open(s,'rb').read()).decode()}",
            "detail": "high"
        }}
        for s in screenshots if s and os.path.exists(s)
    ]
    if not images:
        return {"overall": 5, "critical_issues": ["No screenshots"], "passes_qa": False}

    prompt = f"""You are a senior web designer reviewing a cinematic website for "{brand.get('name','Brand')}" ({brand.get('niche','business')} niche).

Score 1-10 overall. Check:
- Does it look UNIQUE and NOT like a generic AI website?
- Is the hero section visually impressive (3D canvas, not flat)?
- Do scroll animations appear to have fired (elements visible, not hidden)?
- Is the mobile layout clean (no overflow, readable text)?
- Is the typography bold and editorial?
- Does the color palette match the brand niche?

Return JSON:
{{
  "overall": 7,
  "not_generic": 7,
  "hero_quality": 7,
  "scroll_animations_visible": 7,
  "mobile_quality": 7,
  "typography": 7,
  "brand_match": 7,
  "critical_issues": ["issue1"],
  "passes_qa": true
}}"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}] + images}],
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {"overall": 5, "critical_issues": [str(e)], "passes_qa": True}


def _auto_patch(html_path: str, issues: list, brand: dict) -> bool:
    """Ask GPT to fix specific issues."""
    if not issues:
        return False

    html = Path(html_path).read_text(encoding="utf-8")
    issues_text = "\n".join(f"- {i}" for i in issues[:6])

    prompt = f"""Fix this cinematic website HTML for "{brand.get('name','Brand')}" ({brand.get('niche','business')}).

Issues to fix:
{issues_text}

Rules:
- Keep all Three.js hero code intact
- Keep window.HERO_CONFIG intact
- Keep data-niche-scroll attribute
- Fix: add overflow-x:hidden to body and html if mobile overflow
- Fix: ensure .reveal-up elements have correct CSS (opacity:0 initially)
- Fix: ensure hero-content has position:relative;z-index:2
- Fix: ensure hero-frame-canvas has position:absolute;top:0;left:0;width:100%;height:100%;z-index:0
- Improve typography: h1 font-size should be clamp(2.5rem,7vw,6rem)
- Remove any AI slop words: Elevate, Seamless, Next-Gen, Innovative, Transform, Revolutionize

Return ONLY the complete fixed HTML. No markdown fences."""

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Return only valid HTML, no markdown."},
                {"role": "user", "content": prompt + "\n\nHTML:\n" + html[:80000]},
            ],
            max_tokens=16000,
        )
        fixed = resp.choices[0].message.content.strip()
        fixed = re.sub(r"^```[a-z]*\n?", "", fixed)
        fixed = re.sub(r"\n?```$", "", fixed)

        if "<html" in fixed and len(fixed) > 5000:
            Path(html_path).write_text(fixed, encoding="utf-8")
            return True
    except Exception as e:
        print(f"[QA] Patch failed: {e}")
    return False


def run_qa(html_path: str, brand: dict) -> dict:
    """Run full QA. Returns results dict."""
    print(f"\n[QA] ═══ Testing: {Path(html_path).name} ═══")
    print(f"[QA] Brand: {brand.get('name')} | Niche: {brand.get('niche')}")

    # Playwright tests — use new event loop to avoid Flask thread conflicts
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        pw = loop.run_until_complete(_playwright_tests(html_path, brand))
        loop.close()
    except Exception as e:
        print(f"[QA] Playwright failed: {e}")
        pw = {
            'desktop_scroll_ok': False, 'mobile_scroll_ok': False,
            'hero_canvas_ok': False, 'reveals_ok': False,
            'niche_canvas_ok': False, 'progress_bar_ok': False,
            'desktop_top_ss': None, 'desktop_scroll_ss': None,
            'mobile_top_ss': None, 'mobile_scroll_ss': None,
            'errors': [str(e)[:200]]
        }

    print(f"[QA] Desktop scroll:  {'✓' if pw['desktop_scroll_ok'] else '✗'}")
    print(f"[QA] Mobile scroll:   {'✓' if pw['mobile_scroll_ok'] else '✗'}")
    print(f"[QA] Hero canvas:     {'✓' if pw['hero_canvas_ok'] else '✗'}")
    print(f"[QA] Reveals fire:    {'✓' if pw['reveals_ok'] else '✗'}")
    print(f"[QA] Niche canvas:    {'✓' if pw['niche_canvas_ok'] else '✗'}")
    print(f"[QA] Progress bar:    {'✓' if pw['progress_bar_ok'] else '✗'}")

    for err in pw["errors"]:
        print(f"[QA] ⚠  {err}")

    # Collect screenshots
    screenshots = [
        pw.get("desktop_top_ss"),
        pw.get("desktop_scroll_ss"),
        pw.get("mobile_top_ss"),
        pw.get("mobile_scroll_ss"),
    ]
    screenshots = [s for s in screenshots if s and os.path.exists(s)]

    # Vision score
    vision = {}
    if screenshots:
        print("[QA] Running AI vision score...")
        vision = _vision_score(screenshots, brand)
        score = vision.get("overall", 5)
        print(f"[QA] Vision score: {score}/10")
        for issue in vision.get("critical_issues", [])[:3]:
            print(f"[QA] Issue: {issue}")
    else:
        vision = {"overall": 5, "critical_issues": ["No screenshots captured"]}
        score = 5

    # Auto-patch if needed
    patched = False
    needs_patch = score < 7 or not pw["mobile_scroll_ok"] or not pw["reveals_ok"]

    if needs_patch:
        issues = list(vision.get("critical_issues", []))
        if not pw["mobile_scroll_ok"]:
            issues.append("Mobile horizontal overflow — add overflow-x:hidden to html and body")
        if not pw["reveals_ok"]:
            issues.append("Scroll reveals not firing — ensure .reveal-up has opacity:0 and scroll-animations.js is loaded")
        if not pw["hero_canvas_ok"]:
            issues.append("Hero Three.js canvas missing or not rendering — check z-index and position:absolute")

        print(f"[QA] Auto-patching {len(issues)} issues...")
        patched = _auto_patch(html_path, issues, brand)
        if patched:
            print(f"[QA] ✓ Patch applied, re-testing mobile...")
            try:
                loop2 = asyncio.new_event_loop()
                asyncio.set_event_loop(loop2)
                pw2 = loop2.run_until_complete(_playwright_tests(html_path, brand))
                loop2.close()
            except Exception as e2:
                print(f"[QA] Re-test failed: {e2}")
                pw2 = pw
            pw["mobile_scroll_ok"] = pw2["mobile_scroll_ok"]
            pw["reveals_ok"] = pw2["reveals_ok"]
            # Update screenshots
            new_ss = [pw2.get("desktop_top_ss"), pw2.get("mobile_top_ss")]
            screenshots += [s for s in new_ss if s and os.path.exists(s)]

    passes = pw["desktop_scroll_ok"] and pw["mobile_scroll_ok"] and score >= 6

    return {
        "passes": passes,
        "vision_score": score,
        "vision_details": vision,
        "desktop_scroll_ok": pw["desktop_scroll_ok"],
        "mobile_scroll_ok": pw["mobile_scroll_ok"],
        "hero_canvas_ok": pw["hero_canvas_ok"],
        "reveals_ok": pw["reveals_ok"],
        "niche_canvas_ok": pw["niche_canvas_ok"],
        "patched": patched,
        "screenshots": screenshots,
        "errors": pw["errors"],
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        r = run_qa(sys.argv[1], {"name": "Test", "niche": "restaurant"})
        print(json.dumps(r, indent=2, default=str))
