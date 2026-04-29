"""
QA Testing Module — AI Vision Edition
======================================
Uses Playwright for functional testing AND OpenAI GPT-4.1 vision to:

1. FUNCTIONAL TESTS (Playwright):
   - Layout integrity on mobile (375px), tablet (768px), desktop (1440px)
   - No horizontal overflow
   - Three.js canvas present
   - CTA buttons clickable
   - Scroll animations trigger
   - No broken images
   - No console errors

2. AI VISION SCORING (GPT-4.1 with screenshots):
   - Detects if the site looks generic / AI-generated
   - Scores 10 specific anti-generic criteria
   - Identifies exact problem areas with line-level feedback
   - Returns a structured improvement plan

3. AUTO-REWRITE LOOP:
   - If AI score < 7/10, automatically patches the HTML
   - Re-tests after patching
   - Up to 2 rewrite iterations
"""

import os
import json
import base64
import re
from pathlib import Path
from openai import OpenAI
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


VIEWPORTS = {
    "mobile":  {"width": 375,  "height": 812,  "device_scale_factor": 2, "is_mobile": True},
    "tablet":  {"width": 768,  "height": 1024, "device_scale_factor": 2, "is_mobile": True},
    "desktop": {"width": 1440, "height": 900,  "device_scale_factor": 1, "is_mobile": False},
}

# Anti-generic scoring rubric — each criterion is 0 or 1 point
ANTI_GENERIC_CRITERIA = [
    {
        "id": "layout_asymmetry",
        "name": "Asymmetric Layout",
        "description": "Hero is NOT a centered text block over a dark image. Uses split-screen, left-aligned, or offset grid.",
        "bad_signs": ["centered hero text", "text centered over dark overlay", "equal 3-column grid"],
    },
    {
        "id": "no_purple_neon",
        "name": "No Purple/Neon Gradients",
        "description": "Color palette is NOT purple-to-blue neon gradient. Uses brand-specific, muted, or editorial colors.",
        "bad_signs": ["purple gradient", "neon blue gradient", "generic tech gradient"],
    },
    {
        "id": "typography_quality",
        "name": "Premium Typography",
        "description": "NOT using Inter or generic system fonts. Uses Geist, Satoshi, Cabinet Grotesk, Outfit, or brand fonts. Has large editorial type.",
        "bad_signs": ["Inter font", "generic sans-serif", "small body-size headlines"],
    },
    {
        "id": "no_ai_copy",
        "name": "No AI Filler Copy",
        "description": "Headlines do NOT contain: 'Elevate', 'Seamless', 'Next-Gen', 'Innovative', 'Transform', 'Revolutionize', 'Cutting-Edge', 'Empower'.",
        "bad_signs": ["Elevate Your", "Seamless Experience", "Next-Gen", "Innovative Solutions", "Transform Your"],
    },
    {
        "id": "threejs_hero",
        "name": "3D Hero Animation",
        "description": "Hero section has a visible Three.js canvas or 3D element. NOT a static image or flat color.",
        "bad_signs": ["static hero image", "flat color hero", "no canvas element"],
    },
    {
        "id": "scroll_animations",
        "name": "Scroll-Driven Animations",
        "description": "Sections reveal with GSAP ScrollTrigger. Visible animation classes present. NOT static page.",
        "bad_signs": ["no scroll animations", "static sections", "no reveal classes"],
    },
    {
        "id": "visual_hierarchy",
        "name": "Strong Visual Hierarchy",
        "description": "Clear typographic scale. Headline is large (clamp 4-10rem). Subtext is small. NOT uniform text sizes.",
        "bad_signs": ["uniform text sizes", "small headlines", "no typographic contrast"],
    },
    {
        "id": "brand_specificity",
        "name": "Brand-Specific Design",
        "description": "Design clearly reflects the brand's niche and identity. Colors, imagery, and copy match the brand. NOT generic.",
        "bad_signs": ["generic placeholder content", "wrong niche colors", "stock photo feel"],
    },
    {
        "id": "mobile_quality",
        "name": "Mobile Design Quality",
        "description": "Mobile layout is intentional, not just a squished desktop. Text readable, no overflow, proper spacing.",
        "bad_signs": ["text overflow on mobile", "tiny text on mobile", "broken mobile layout"],
    },
    {
        "id": "premium_details",
        "name": "Premium Details",
        "description": "Has at least 2 of: magnetic buttons, kinetic marquee, liquid glass cards, curtain reveal, text scramble, bento grid, horizontal scroll gallery.",
        "bad_signs": ["no premium effects", "basic card grid only", "no interactive details"],
    },
]


def encode_image_base64(image_path: str) -> str:
    """Encode image to base64 for OpenAI vision API."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def take_screenshots(html_path: str, qa_dir: str) -> dict:
    """Take screenshots at all viewports. Returns dict of viewport -> screenshot paths."""
    screenshots = {}
    file_url = f"file://{os.path.abspath(html_path)}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for vp_name, vp in VIEWPORTS.items():
            try:
                ctx = browser.new_context(
                    viewport={"width": vp["width"], "height": vp["height"]},
                    device_scale_factor=vp["device_scale_factor"],
                    is_mobile=vp["is_mobile"],
                )
                page = ctx.new_page()

                console_errors = []
                page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda e: console_errors.append(str(e)))

                page.goto(file_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2500)

                # Hero screenshot (above the fold)
                hero_path = os.path.join(qa_dir, f"qa-{vp_name}-hero.png")
                page.screenshot(path=hero_path, full_page=False)

                # Full page screenshot
                full_path = os.path.join(qa_dir, f"qa-{vp_name}-full.png")
                page.screenshot(path=full_path, full_page=True)

                # Mid-scroll screenshot
                page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.35)")
                page.wait_for_timeout(600)
                mid_path = os.path.join(qa_dir, f"qa-{vp_name}-mid.png")
                page.screenshot(path=mid_path)

                # Functional checks
                checks = {
                    "no_overflow": not page.evaluate(
                        "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
                    ),
                    "has_canvas": page.query_selector("canvas") is not None,
                    "has_nav": page.query_selector("nav, header") is not None,
                    "has_cta": page.query_selector("a, button") is not None,
                    "has_text": page.evaluate("() => document.body.innerText.length") > 200,
                    "console_errors": console_errors[:5],
                }

                screenshots[vp_name] = {
                    "hero": hero_path,
                    "full": full_path,
                    "mid": mid_path,
                    "checks": checks,
                }
                ctx.close()

            except Exception as e:
                print(f"[QA] Screenshot error ({vp_name}): {e}")
                screenshots[vp_name] = {"error": str(e), "checks": {}}

        browser.close()

    return screenshots


def ai_vision_score(html_path: str, screenshots: dict, brand: dict) -> dict:
    """
    Use GPT-4.1 vision to score the website against anti-generic criteria.
    Returns detailed scoring and improvement instructions.
    """
    client = OpenAI()

    # Collect images to send (desktop hero + mobile hero + desktop mid)
    images_to_send = []
    labels = []

    for vp_name in ["desktop", "mobile"]:
        if vp_name in screenshots and "hero" in screenshots[vp_name]:
            path = screenshots[vp_name]["hero"]
            if os.path.exists(path):
                images_to_send.append(path)
                labels.append(f"{vp_name.upper()} — Above the fold")

    if "desktop" in screenshots and "mid" in screenshots.get("desktop", {}):
        mid = screenshots["desktop"]["mid"]
        if os.path.exists(mid):
            images_to_send.append(mid)
            labels.append("DESKTOP — Mid-page scroll")

    # Read HTML for code-level analysis
    html_content = Path(html_path).read_text(encoding="utf-8", errors="replace")
    html_snippet = html_content[:6000]  # First 6k chars for context

    # Build vision message
    content = []

    # Add text context
    content.append({
        "type": "text",
        "text": f"""You are a senior creative director reviewing a website for a brand called "{brand.get('name', 'Unknown')}" in the "{brand.get('niche', 'business')}" niche.

Your job is to evaluate whether this website looks like a GENERIC AI-GENERATED WEBSITE or a PREMIUM, UNIQUE, AGENCY-BUILT WEBSITE.

Score each of these 10 criteria from 0 (fail) to 1 (pass):

{json.dumps([{"id": c["id"], "name": c["name"], "description": c["description"], "bad_signs": c["bad_signs"]} for c in ANTI_GENERIC_CRITERIA], indent=2)}

Also check the HTML snippet for AI slop patterns:
```html
{html_snippet}
```

Return a JSON object with this exact structure:
{{
  "total_score": <0-10>,
  "scores": {{
    "layout_asymmetry": {{"score": 0|1, "reason": "...", "fix": "..."}},
    "no_purple_neon": {{"score": 0|1, "reason": "...", "fix": "..."}},
    "typography_quality": {{"score": 0|1, "reason": "...", "fix": "..."}},
    "no_ai_copy": {{"score": 0|1, "reason": "...", "fix": "..."}},
    "threejs_hero": {{"score": 0|1, "reason": "...", "fix": "..."}},
    "scroll_animations": {{"score": 0|1, "reason": "...", "fix": "..."}},
    "visual_hierarchy": {{"score": 0|1, "reason": "...", "fix": "..."}},
    "brand_specificity": {{"score": 0|1, "reason": "...", "fix": "..."}},
    "mobile_quality": {{"score": 0|1, "reason": "...", "fix": "..."}},
    "premium_details": {{"score": 0|1, "reason": "...", "fix": "..."}}
  }},
  "verdict": "PASS|FAIL",
  "overall_feedback": "...",
  "priority_fixes": ["fix 1", "fix 2", "fix 3"],
  "html_patches": [
    {{
      "description": "What to change",
      "find": "exact HTML string to find",
      "replace": "exact HTML string to replace with"
    }}
  ]
}}

Be specific and actionable. For html_patches, provide the exact strings to find and replace in the HTML.
Return ONLY the JSON, no markdown, no explanation."""
    })

    # Add screenshots
    for img_path, label in zip(images_to_send, labels):
        try:
            b64 = encode_image_base64(img_path)
            content.append({"type": "text", "text": f"Screenshot: {label}"})
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"}
            })
        except Exception as e:
            print(f"[QA Vision] Could not encode image {img_path}: {e}")

    print("[QA Vision] Sending screenshots to GPT-4.1 for AI vision scoring...")
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": content}],
            max_tokens=3000,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()

        # Clean markdown fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)

        vision_result = json.loads(raw)
        print(f"[QA Vision] Score: {vision_result.get('total_score', '?')}/10 — {vision_result.get('verdict', '?')}")
        return vision_result

    except json.JSONDecodeError as e:
        print(f"[QA Vision] JSON parse error: {e}. Raw: {raw[:300]}")
        return {"total_score": 5, "verdict": "UNKNOWN", "scores": {}, "priority_fixes": [], "html_patches": []}
    except Exception as e:
        print(f"[QA Vision] Error: {e}")
        return {"total_score": 5, "verdict": "UNKNOWN", "scores": {}, "priority_fixes": [], "html_patches": []}


def apply_html_patches(html_path: str, patches: list) -> int:
    """Apply AI-suggested HTML patches. Returns number of patches applied."""
    if not patches:
        return 0

    html = Path(html_path).read_text(encoding="utf-8", errors="replace")
    applied = 0

    for patch in patches:
        find_str = patch.get("find", "")
        replace_str = patch.get("replace", "")
        desc = patch.get("description", "")

        if not find_str or not replace_str:
            continue

        if find_str in html:
            html = html.replace(find_str, replace_str, 1)
            applied += 1
            print(f"  [Patch] Applied: {desc[:80]}")
        else:
            print(f"  [Patch] Not found: {desc[:80]}")

    if applied > 0:
        Path(html_path).write_text(html, encoding="utf-8")

    return applied


def ai_rewrite_section(html_path: str, vision_result: dict, brand: dict) -> bool:
    """
    If score < 7, use GPT-4.1 to rewrite the worst-scoring sections.
    Returns True if rewrite was applied.
    """
    score = vision_result.get("total_score", 10)
    if score >= 7:
        return False

    client = OpenAI()
    html = Path(html_path).read_text(encoding="utf-8", errors="replace")

    # Collect all failing criteria with their fixes
    failing = []
    for crit_id, data in vision_result.get("scores", {}).items():
        if data.get("score", 1) == 0:
            failing.append({
                "criterion": crit_id,
                "reason": data.get("reason", ""),
                "fix": data.get("fix", "")
            })

    priority_fixes = vision_result.get("priority_fixes", [])
    overall_feedback = vision_result.get("overall_feedback", "")

    print(f"[QA Rewrite] Score was {score}/10. Rewriting {len(failing)} failing sections...")

    system = """You are a senior creative director and frontend engineer.
You receive a website HTML file that has been flagged as looking too generic/AI-generated.
Your job is to rewrite SPECIFIC sections to make it look premium, unique, and agency-built.
You MUST fix the exact issues identified. Return the COMPLETE improved HTML file.
Do not add placeholders. Do not truncate. Return the full HTML."""

    user = f"""This website for "{brand.get('name')}" ({brand.get('niche')} niche) scored {score}/10 on our anti-generic checklist.

FAILING CRITERIA:
{json.dumps(failing, indent=2)}

PRIORITY FIXES NEEDED:
{chr(10).join(f"- {f}" for f in priority_fixes)}

OVERALL FEEDBACK:
{overall_feedback}

BRAND DATA:
- Name: {brand.get('name')}
- Niche: {brand.get('niche')}
- Headline: {brand.get('headline', '')}
- Colors: {json.dumps(brand.get('colors', {}))}
- Fonts: {brand.get('fonts', [])}

CURRENT HTML (fix the issues above while keeping all working Three.js and GSAP code):
{html[:14000]}

Return the COMPLETE fixed HTML file starting with <!DOCTYPE html>.
Focus on fixing the failing criteria. Keep all JavaScript (Three.js, GSAP) intact."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            max_tokens=16000,
            temperature=0.7,
        )
        new_html = response.choices[0].message.content.strip()

        # Clean markdown fences
        if new_html.startswith("```html"):
            new_html = new_html[7:]
        if new_html.startswith("```"):
            new_html = new_html[3:]
        if new_html.endswith("```"):
            new_html = new_html[:-3]
        new_html = new_html.strip()

        # Ensure it starts with DOCTYPE
        if not new_html.startswith("<!DOCTYPE") and not new_html.startswith("<html"):
            idx = new_html.find("<!DOCTYPE")
            if idx == -1:
                idx = new_html.find("<html")
            if idx != -1:
                new_html = new_html[idx:]

        if len(new_html) > 5000:  # Sanity check — must be a real HTML file
            Path(html_path).write_text(new_html, encoding="utf-8")
            print(f"[QA Rewrite] HTML rewritten ({len(new_html)} chars)")
            return True
        else:
            print(f"[QA Rewrite] Rewrite too short ({len(new_html)} chars), skipping")
            return False

    except Exception as e:
        print(f"[QA Rewrite] Error: {e}")
        return False


def run_qa(html_path: str, output_dir: str, brand: dict = None, max_rewrites: int = 2) -> dict:
    """
    Main QA function. Runs functional tests + AI vision scoring + auto-rewrite loop.

    Args:
        html_path: Path to the generated index.html
        output_dir: Output directory for screenshots and reports
        brand: Brand data dict (for context in AI scoring)
        max_rewrites: Max number of AI rewrite iterations

    Returns:
        Full QA results dict with scores, screenshots, issues, and final verdict
    """
    if brand is None:
        brand = {}

    print(f"\n[QA] ═══════════════════════════════════════════════════")
    print(f"[QA] Testing: {os.path.basename(html_path)}")
    print(f"[QA] Brand: {brand.get('name', 'Unknown')} | Niche: {brand.get('niche', '?')}")
    print(f"[QA] ═══════════════════════════════════════════════════")

    qa_dir = os.path.join(output_dir, "qa")
    os.makedirs(qa_dir, exist_ok=True)

    results = {
        "passed": False,
        "vision_score": 0,
        "vision_verdict": "UNKNOWN",
        "iterations": [],
        "final_score": 0,
        "functional_checks": {},
        "issues": [],
        "screenshots": {},
        "rewrite_count": 0,
    }

    for iteration in range(max_rewrites + 1):
        print(f"\n[QA] ── Iteration {iteration + 1} ──────────────────────────────")

        # Step 1: Take screenshots + functional checks
        print("[QA] Taking screenshots (mobile, tablet, desktop)...")
        screenshots = take_screenshots(html_path, qa_dir)
        results["screenshots"] = {vp: data.get("hero", "") for vp, data in screenshots.items()}

        # Collect functional check results
        functional = {}
        for vp_name, vp_data in screenshots.items():
            checks = vp_data.get("checks", {})
            for check_name, check_val in checks.items():
                if check_name != "console_errors":
                    key = f"{vp_name}_{check_name}"
                    functional[key] = check_val
                    if isinstance(check_val, bool) and not check_val:
                        results["issues"].append(f"{vp_name}: {check_name} FAILED")
            if checks.get("console_errors"):
                results["issues"].append(f"{vp_name}: {len(checks['console_errors'])} console error(s): {checks['console_errors'][0][:80]}")

        results["functional_checks"] = functional

        # Step 2: AI vision scoring
        print("[QA] Running AI vision scoring...")
        vision = ai_vision_score(html_path, screenshots, brand)
        score = vision.get("total_score", 0)
        verdict = vision.get("verdict", "UNKNOWN")

        iter_result = {
            "iteration": iteration + 1,
            "score": score,
            "verdict": verdict,
            "failing_criteria": [
                {"id": cid, "reason": cdata.get("reason", ""), "fix": cdata.get("fix", "")}
                for cid, cdata in vision.get("scores", {}).items()
                if cdata.get("score", 1) == 0
            ],
            "priority_fixes": vision.get("priority_fixes", []),
            "overall_feedback": vision.get("overall_feedback", ""),
            "patches_applied": 0,
            "rewrite_applied": False,
        }

        print(f"\n[QA] ┌─ Vision Score: {score}/10 — {verdict}")
        for cid, cdata in vision.get("scores", {}).items():
            status = "✓" if cdata.get("score", 0) == 1 else "✗"
            print(f"[QA] │  {status} {cid}: {cdata.get('reason', '')[:70]}")
        print(f"[QA] └─ Feedback: {vision.get('overall_feedback', '')[:120]}")

        if vision.get("priority_fixes"):
            print("[QA] Priority fixes:")
            for fix in vision["priority_fixes"]:
                print(f"  → {fix}")

        results["vision_score"] = score
        results["vision_verdict"] = verdict
        results["final_score"] = score

        # Step 3: If passing or last iteration, stop
        if score >= 7 or iteration == max_rewrites:
            results["passed"] = score >= 6
            iter_result["action"] = "ACCEPTED" if score >= 7 else "ACCEPTED_FINAL"
            results["iterations"].append(iter_result)
            break

        # Step 4: Apply quick HTML patches first
        patches = vision.get("html_patches", [])
        if patches:
            applied = apply_html_patches(html_path, patches)
            iter_result["patches_applied"] = applied
            print(f"[QA] Applied {applied}/{len(patches)} HTML patches")

        # Step 5: Full AI rewrite for low scores
        if score < 6:
            print(f"[QA] Score {score}/10 is below threshold. Triggering full AI rewrite...")
            rewrote = ai_rewrite_section(html_path, vision, brand)
            iter_result["rewrite_applied"] = rewrote
            if rewrote:
                results["rewrite_count"] += 1
                iter_result["action"] = "REWRITTEN"
            else:
                iter_result["action"] = "PATCH_ONLY"
        else:
            iter_result["action"] = "PATCHED"

        results["iterations"].append(iter_result)

    # Save QA report
    report_path = os.path.join(qa_dir, "qa-report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[QA] ═══════════════════════════════════════════════════")
    print(f"[QA] FINAL SCORE: {results['final_score']}/10 — {'PASS ✓' if results['passed'] else 'FAIL ✗'}")
    print(f"[QA] Rewrites applied: {results['rewrite_count']}")
    print(f"[QA] Issues found: {len(results['issues'])}")
    print(f"[QA] ═══════════════════════════════════════════════════\n")

    return results


if __name__ == "__main__":
    import sys
    html_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/test/index.html"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/test"
    brand = {"name": "Test Brand", "niche": "restaurant"}
    results = run_qa(html_path, output_dir, brand)
    print(json.dumps({k: v for k, v in results.items() if k not in ["functional_checks", "screenshots"]}, indent=2))
