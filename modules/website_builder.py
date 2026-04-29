"""
Website Builder v3 — Separation of Concerns
=============================================
The AI generates HTML structure + CSS ONLY.
All JavaScript is injected programmatically AFTER generation.
This guarantees:
- Three.js loads before hero script (no race conditions)
- GSAP loads before scroll triggers
- Reveal class (.is-revealed) is consistent everywhere
- No AI hallucinating broken JS
"""

import os
import json
import re
from openai import OpenAI
from pathlib import Path
from modules.image_generator import fix_images_with_nano_banana, fix_background_images_with_nano_banana

# ── Taste-Skill Design Rules ─────────────────────────────────────────────────
TASTE_SKILL_RULES = """
## TASTE-SKILL DESIGN RULES (MANDATORY)

### ❌ FORBIDDEN — NEVER DO THESE:
- NO centered hero with text over dark image
- NO purple/blue neon gradients
- NO Inter font
- NO 3-column equal-height card layouts
- NO generic copy: "Elevate", "Seamless", "Next-Gen", "Revolutionize", "Transform", "Innovative", "Cutting-Edge"
- NO pure black (#000000) — use zinc-950 (#09090b) or charcoal (#0d0d0d)
- NO Unsplash image links or generic stock photo placeholders
- NO oversaturated accent colors (saturation must be < 80%)
- NO flat, static hero sections
- NO symmetrical, centered layouts
- NO generic "card grid" sections

### ✅ MANDATORY DESIGN RULES:
- Fonts: Geist, Satoshi, Cabinet Grotesk, Outfit, or Syne — NEVER Inter
- Asymmetric layouts: split-screen, left-aligned, offset grids, editorial
- Max 1 accent color, saturation < 80%
- Liquid glass: backdrop-filter: blur(12px) + 1px inner border + inner shadow
- Magnetic buttons: class="magnetic-btn" on all CTAs
- Staggered orchestration for all lists/grids (transition-delay)
- Hardware-accelerated animations (transform + opacity ONLY)
- min-height: 100dvh for hero (NEVER height: 100vh)
- Tinted shadows matching background hue (NOT black shadows)
- Scroll progress bar: <div id="scroll-progress"></div> at top of body
- Kinetic marquee for social proof / brand keywords
- Count-up animations: class="count-up" data-target="500" data-suffix="+"
- All reveal elements: class="reveal-up" (NOT reveal, NOT animated)

### ✅ MANDATORY SECTIONS (in this order):
1. Sticky nav — blur backdrop, brand name left, links right, CTA pill
2. HERO — id="hero-scroll-section" height:400vh, inner .hero-sticky div
3. Brand statement — asymmetric split, large editorial text
4. Services/features — id="services" data-niche-scroll="NICHE" bento grid or zig-zag
5. Stats — count-up numbers, kinetic marquee
6. Gallery/showcase — horizontal scroll
7. CTA section — full-width, cinematic background
8. Footer — minimal

### ✅ HERO STRUCTURE (EXACT — DO NOT CHANGE):
<section id="hero-scroll-section">
  <div class="hero-sticky">
    <!-- JS will inject canvas here automatically -->
    <div class="hero-content">
      <p class="hero-eyebrow">...</p>
      <h1 class="hero-headline text-scramble">HEADLINE<br>LINE TWO</h1>
      <p class="hero-sub">...</p>
      <a href="#services" class="hero-cta magnetic-btn">CTA →</a>
    </div>
  </div>
</section>

### ✅ REVEAL ANIMATION CLASS (EXACT):
- Use class="reveal-up" on ALL section elements that should animate in
- JS will automatically add class="is-revealed" when they scroll into view
- CSS must define: .reveal-up { opacity: 0; transform: translateY(40px); transition: opacity 0.7s, transform 0.7s; }
- CSS must define: .reveal-up.is-revealed { opacity: 1; transform: translateY(0); }

### ✅ CINEMATIC EFFECTS (ALL REQUIRED):
- Mesh gradient animated background on hero
- Text scramble: class="text-scramble" on hero headline (JS handles it)
- Magnetic CTA buttons: class="magnetic-btn" (JS handles mousemove)
- Parallax images: class="parallax-img" (JS handles scroll)
- Kinetic marquee (CSS animation, infinite)
- Horizontal scroll gallery
- Glassmorphism cards with backdrop-filter
- Gradient text: background: linear-gradient; -webkit-background-clip: text
- CSS scroll-driven animations: animation-timeline: scroll() where supported
"""

SYSTEM_PROMPT = """You are a world-class creative director and senior frontend engineer.
You build cinematic, premium websites that look NOTHING like typical AI-generated sites.
Your output is a complete HTML file with ALL CSS inline in <style> tags.
DO NOT include ANY JavaScript — the JS will be added separately.
You follow the taste-skill design rules strictly.
Every website you build is unique, visually striking, and tailored to the specific brand.
You take inspiration from award-winning sites on Awwwards, Behance, and Dribbble.
You NEVER produce generic, template-looking output.
IMPORTANT: Output ONLY the HTML. No explanation. No markdown fences."""


def read_module(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return f"// Module not found: {e}"


def inject_scripts(html: str, brand: dict, modules_dir: Path) -> str:
    """
    Programmatically inject all JavaScript into the HTML.
    This runs AFTER the AI generates the HTML structure.
    Guarantees correct loading order and no race conditions.
    """
    accent = brand.get("colors", {}).get("accent", "#e63946")
    bg_a = brand.get("colors", {}).get("background", "#0a0a0f")
    bg_b = brand.get("colors", {}).get("secondary", "#1a0a2e")
    niche = brand.get("niche", "business")

    hero_js = read_module(str(modules_dir / "hero-scroll-frame.js"))
    niche_js = read_module(str(modules_dir / "niche-scroll-animations.js"))
    scroll_js = read_module(str(modules_dir / "scroll-animations.js"))

    # Remove any existing script tags the AI may have added
    html = re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.DOTALL)

    # Remove defer from any remaining CDN links (shouldn't exist but safety)
    html = re.sub(r'\s+defer\b', '', html, flags=re.IGNORECASE)

    # Build scripts using concatenation to avoid f-string conflicts with JS curly braces
    hero_config = (
        'window.__HERO_FRAME_CONFIG__ = {\n'
        f'  sectionId: \'hero-scroll-section\',\n'
        f'  accentColor: \'{accent}\',\n'
        f'  bgColorA: \'{bg_a}\',\n'
        f'  bgColorB: \'{bg_b}\',\n'
        f'  niche: \'{niche}\',\n'
        '  scrollMultiplier: 4,\n'
        '};\n'
        f'window.BRAND_DATA = {{\n'
        f'  name: {json.dumps(brand.get("name", "Brand"))},\n'
        f'  niche: {json.dumps(niche)},\n'
        f'  accentColor: \'{accent}\',\n'
        '};'
    )

    scripts = (
        '\n<!-- ═══ SCRIPTS (injected programmatically — DO NOT EDIT ORDER) ═══ -->\n\n'
        '<!-- 1. Three.js — must load first, synchronously -->\n'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>\n\n'
        '<!-- 2. GSAP + ScrollTrigger — synchronous -->\n'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>\n'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js"></script>\n\n'
        '<!-- 3. Hero config — must be set BEFORE hero script -->\n'
        '<script>\n' + hero_config + '\n</script>\n\n'
        '<!-- 4. Hero scroll-driven Three.js animation -->\n'
        '<script>\n' + hero_js + '\n</script>\n\n'
        '<!-- 5. Niche-specific scroll canvas animations -->\n'
        '<script>\n' + niche_js + '\n</script>\n\n'
        '<!-- 6. Section reveals + count-up + progress bar (IntersectionObserver) -->\n'
         '<script>\n' + scroll_js + '\n</script>\n\n'
        '<!-- 7. Magnetic buttons -->'
    )
    scripts += """
<script>
(function() {{
  function initMagnetic() {{
    document.querySelectorAll('.magnetic-btn').forEach(function(btn) {{
      btn.addEventListener('mousemove', function(e) {{
        var r = btn.getBoundingClientRect();
        var x = (e.clientX - r.left - r.width/2) * 0.3;
        var y = (e.clientY - r.top  - r.height/2) * 0.3;
        btn.style.transform = 'translate(' + x + 'px,' + y + 'px)';
        btn.style.transition = 'transform 0.12s ease';
      }});
      btn.addEventListener('mouseleave', function() {{
        btn.style.transform = '';
        btn.style.transition = 'transform 0.5s cubic-bezier(.22,1,.36,1)';
      }});
    }});
  }}
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', initMagnetic);
  }} else {{
    initMagnetic();
  }}
}})();
</script>

<!-- 8. Scroll progress bar -->
<script>
(function() {{
  var bar = document.getElementById('scroll-progress');
  if (!bar) return;
  function update() {{
    var p = window.scrollY / Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    bar.style.width = (p * 100) + '%';
  }}
  window.addEventListener('scroll', update, {{ passive: true }});
  window.addEventListener('touchmove', update, {{ passive: true }});
}})();
</script>

<!-- 9. Count-up stats -->
<script>
(function() {{
  function initCountUp() {{
    var els = document.querySelectorAll('.count-up[data-target]');
    if (!els.length) return;
    var io = new IntersectionObserver(function(entries) {{
      entries.forEach(function(e) {{
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        var el = e.target;
        var target = parseFloat(el.getAttribute('data-target')) || 0;
        var suffix = el.getAttribute('data-suffix') || '';
        var prefix = el.getAttribute('data-prefix') || '';
        var dur = 1800, start = performance.now();
        function step(now) {{
          var p = Math.min((now - start) / dur, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          var val = target * eased;
          el.textContent = prefix + (Number.isInteger(target) ? Math.round(val) : val.toFixed(1)) + suffix;
          if (p < 1) requestAnimationFrame(step);
        }}
        requestAnimationFrame(step);
      }});
    }}, {{ threshold: 0.3 }});
    els.forEach(function(el) {{ io.observe(el); }});
  }}
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', initCountUp);
  }} else {{
    initCountUp();
  }}
}})();
</script>

<!-- 10. Reveal on scroll (IntersectionObserver — works on all devices) -->
<script>
(function() {{
  function initReveals() {{
    var els = document.querySelectorAll('.reveal-up, .reveal-left, .reveal-right, .reveal-scale');
    if (!els.length) return;
    var io = new IntersectionObserver(function(entries) {{
      entries.forEach(function(e) {{
        if (e.isIntersecting) {{
          e.target.classList.add('is-revealed');
          io.unobserve(e.target);
        }}
      }});
    }}, {{ threshold: 0.08, rootMargin: '0px 0px -20px 0px' }});
    els.forEach(function(el) {{ io.observe(el); }});
  }}
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', initReveals);
  }} else {{
    initReveals();
  }}
}})();
</script>
"""

    # Insert scripts before </body>
    if "</body>" in html:
        html = html.replace("</body>", scripts + "\n</body>")
    else:
        html += scripts

    return html


def fix_reveal_classes(html: str) -> str:
    """Ensure reveal CSS uses .is-revealed not .visible or .animated."""
    # Fix CSS: .reveal-up.visible -> .reveal-up.is-revealed
    html = re.sub(r'\.reveal-up\.visible\b', '.reveal-up.is-revealed', html)
    html = re.sub(r'\.reveal-up\.animated\b', '.reveal-up.is-revealed', html)
    html = re.sub(r'\.reveal-up\.active\b', '.reveal-up.is-revealed', html)
    html = re.sub(r'\.reveal-left\.visible\b', '.reveal-left.is-revealed', html)
    html = re.sub(r'\.reveal-right\.visible\b', '.reveal-right.is-revealed', html)

    # Ensure the is-revealed CSS rule exists
    if '.is-revealed' not in html:
        reveal_css = """
.reveal-up.is-revealed,
.reveal-left.is-revealed,
.reveal-right.is-revealed,
.reveal-scale.is-revealed {
  opacity: 1 !important;
  transform: none !important;
}"""
        html = html.replace('</style>', reveal_css + '\n</style>', 1)

    return html


def fix_mobile_overflow(html: str) -> str:
    """Ensure body and html have overflow-x: hidden."""
    if 'overflow-x: hidden' not in html and 'overflow-x:hidden' not in html:
        html = html.replace(
            'body {',
            'html, body { overflow-x: hidden; }\nbody {',
            1
        )
    return html


def inject_critical_overrides(html: str, brand: dict) -> str:
    """
    Inject a <style> block with !important overrides for all critical layout rules.
    This runs LAST and guarantees correct layout regardless of AI output.
    """
    accent = brand.get('colors', {}).get('accent', '#e63946')
    bg = brand.get('colors', {}).get('background', '#0d0d0d')

    critical_css = f"""
<!-- CRITICAL OVERRIDES — injected by pipeline post-processor -->
<style id="pipeline-critical-overrides">
/* ── Mobile safety ── */
html, body {{
  overflow-x: hidden !important;
  max-width: 100vw !important;
}}
* {{
  max-width: 100% !important;
  box-sizing: border-box !important;
}}
img, video, canvas {{
  max-width: 100% !important;
  height: auto;
}}

/* ── Hero scroll section ── */
#hero-scroll-section {{
  position: relative !important;
  height: 400vh !important;
  overflow: hidden !important;
}}

/* ── Hero sticky — MUST be sticky + flex centered ── */
.hero-sticky {{
  position: sticky !important;
  top: 0 !important;
  height: 100dvh !important;
  width: 100% !important;
  overflow: hidden !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
}}

/* ── Hero canvas — full bleed behind content ── */
#hero-frame-canvas {{
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  max-width: none !important;
  z-index: 0 !important;
}}

/* ── Hero content — above canvas ── */
.hero-content {{
  position: relative !important;
  z-index: 2 !important;
  padding: 0 clamp(1.5rem, 5vw, 6rem) !important;
  max-width: min(900px, 90vw) !important;
  width: 100% !important;
}}

/* ── Hero headline — never overflow ── */
.hero-headline {{
  white-space: normal !important;
  word-break: break-word !important;
  overflow-wrap: break-word !important;
  font-size: clamp(2.5rem, 7vw, 6.5rem) !important;
  line-height: 1.05 !important;
  max-width: 100% !important;
}}

/* ── Reveal animations ── */
.reveal-up {{
  opacity: 0 !important;
  transform: translateY(40px) !important;
  transition: opacity 0.7s ease, transform 0.7s ease !important;
}}
.reveal-up.is-revealed {{
  opacity: 1 !important;
  transform: translateY(0) !important;
}}
.reveal-left {{
  opacity: 0 !important;
  transform: translateX(-40px) !important;
  transition: opacity 0.7s ease, transform 0.7s ease !important;
}}
.reveal-left.is-revealed {{
  opacity: 1 !important;
  transform: translateX(0) !important;
}}
.reveal-right {{
  opacity: 0 !important;
  transform: translateX(40px) !important;
  transition: opacity 0.7s ease, transform 0.7s ease !important;
}}
.reveal-right.is-revealed {{
  opacity: 1 !important;
  transform: translateX(0) !important;
}}

/* ── Scroll progress bar ── */
#scroll-progress {{
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  height: 2px !important;
  background: {accent} !important;
  z-index: 9999 !important;
  transition: width 0.1s linear !important;
  width: 0 !important;
}}

/* ── Mobile nav ── */
@media (max-width: 768px) {{
  nav, header {{
    padding: 1rem 1.25rem !important;
  }}
  .hero-content {{
    padding: 0 1.25rem !important;
  }}
  .hero-headline {{
    font-size: clamp(2rem, 10vw, 3.5rem) !important;
  }}
}}
</style>
"""

    # Insert before </head>
    if "</head>" in html:
        html = html.replace("</head>", critical_css + "\n</head>", 1)
    else:
        html = critical_css + html

    return html


def fix_hero_structure(html: str) -> str:
    """Legacy — kept for compatibility. Real fixes are in inject_critical_overrides."""
    return html


# Niche-specific Unsplash image collections (real working URLs)
NICHE_IMAGES = {
    'restaurant': [
        'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&q=80',
        'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800&q=80',
        'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&q=80',
        'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80',
        'https://images.unsplash.com/photo-1600891964092-4316c288032e?w=800&q=80',
    ],
    'fitness': [
        'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800&q=80',
        'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&q=80',
        'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=800&q=80',
        'https://images.unsplash.com/photo-1549060279-7e168fcee0c2?w=800&q=80',
        'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=800&q=80',
    ],
    'beauty': [
        'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=800&q=80',
        'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=800&q=80',
        'https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=800&q=80',
        'https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=800&q=80',
        'https://images.unsplash.com/photo-1512290923902-8a9f81dc236c?w=800&q=80',
    ],
    'tech_saas': [
        'https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80',
        'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=800&q=80',
        'https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&q=80',
        'https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800&q=80',
        'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&q=80',
    ],
    'hotel': [
        'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&q=80',
        'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800&q=80',
        'https://images.unsplash.com/photo-1582719508461-905c673771fd?w=800&q=80',
        'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=800&q=80',
        'https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=800&q=80',
    ],
    'default': [
        'https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=800&q=80',
        'https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&q=80',
        'https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=800&q=80',
        'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&q=80',
        'https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80',
    ],
}


def fix_broken_images(html: str, brand: dict) -> str:
    """
    Replace any broken/fake image URLs with real Unsplash images matched to niche.
    Also replace empty src attributes.
    """
    niche = brand.get('niche', 'default')
    # Map niche variants to image sets
    if 'restaurant' in niche or 'food' in niche or 'cafe' in niche or 'coffee' in niche:
        images = NICHE_IMAGES['restaurant']
    elif 'fitness' in niche or 'gym' in niche or 'sport' in niche:
        images = NICHE_IMAGES['fitness']
    elif 'beauty' in niche or 'skin' in niche or 'cosmetic' in niche or 'aesop' in niche.lower():
        images = NICHE_IMAGES['beauty']
    elif 'tech' in niche or 'saas' in niche or 'software' in niche or 'app' in niche:
        images = NICHE_IMAGES['tech_saas']
    elif 'hotel' in niche or 'luxury' in niche or 'hospitality' in niche:
        images = NICHE_IMAGES['hotel']
    else:
        images = NICHE_IMAGES['default']

    img_idx = [0]  # mutable counter for closure

    def replace_img_src(match):
        full_tag = match.group(0)
        src = match.group(1)
        # Only replace if the src looks fake/broken (not a real CDN or data URI)
        is_fake = (
            not src.startswith('data:') and
            not src.startswith('https://images.unsplash.com') and
            not src.startswith('https://cdn.') and
            not src.startswith('https://upload.wikimedia') and
            (
                'placeholder' in src.lower() or
                'example.com' in src or
                src == '' or src == '#' or
                # Fake CDN patterns the AI generates
                re.search(r'assets\.[a-z]+\.(com|net|org)', src) is not None
            )
        )
        if is_fake:
            real_src = images[img_idx[0] % len(images)]
            img_idx[0] += 1
            return full_tag.replace(src, real_src)
        return full_tag

    html = re.sub(r'<img[^>]+src=["\']([^"\']*)["\'][^>]*>', replace_img_src, html)
    return html


def fix_gallery_overflow(html: str) -> str:
    """Fix horizontal gallery overflow by constraining padding and adding overflow wrapper."""
    # Replace large clamp padding on gallery that causes overflow
    html = re.sub(
        r'(\.gallery-scroll\s*\{[^}]*padding(?:-left|-right)?\s*:\s*)clamp\([^)]+\)',
        r'\g<1>2rem',
        html
    )
    return html


def remove_duplicate_countup(html: str) -> str:
    """Remove inline count-up JS generated by AI to avoid duplicate with injected version."""
    # Remove any inline <script> blocks that contain countUp or count-up logic
    # but are NOT from our injected scripts (which have specific markers)
    def remove_inline_countup(m):
        script_content = m.group(0)
        # Keep our injected scripts (they have specific markers)
        if 'CINEMATIC PIPELINE' in script_content or 'initCountUp' in script_content:
            return script_content
        # Remove AI-generated count-up scripts
        if 'countUp' in script_content or ('count-up' in script_content and 'data-target' in script_content):
            return '<!-- count-up removed: handled by pipeline -->'
        return script_content
    html = re.sub(r'<script[^>]*>.*?</script>', remove_inline_countup, html, flags=re.DOTALL)
    return html


def build_website(brand: dict, reference: dict, video_result: dict, output_dir: str) -> str:
    """
    Generate a complete cinematic website HTML file.
    Returns path to the generated HTML file.
    """
    print(f"[Website Builder] Building website for: {brand.get('name', 'Unknown')}")

    client = OpenAI()
    modules_dir = Path(__file__).parent.parent / "cinematic-modules"

    niche = brand.get('niche', 'business')
    accent = brand.get('colors', {}).get('accent', '#e63946')
    bg_a = brand.get('colors', {}).get('background', '#0a0a0f')
    bg_b = brand.get('colors', {}).get('secondary', '#1a0a2e')
    name = brand.get('name', 'Brand')
    headline = brand.get('headline', f'Premium {niche.title()}')
    tagline = brand.get('tagline', 'Excellence in every detail')
    services = brand.get('services', ['Service 1', 'Service 2', 'Service 3'])
    fonts = brand.get('fonts', ['Geist', 'Satoshi'])

    # Reference design context
    ref_context = ""
    if reference.get('design_md'):
        ref_context = f"\n\n## REFERENCE DESIGN SYSTEM\nStudy this and incorporate its best patterns:\n{reference['design_md'][:2000]}"
    if reference.get('colors'):
        ref_context += f"\n\nReference Colors: {json.dumps(reference['colors'])[:400]}"

    user_prompt = f"""Build a complete, stunning, cinematic website for this brand.
Make it look like it was built by the best creative agency in the world.
Output ONLY the HTML file (<!DOCTYPE html> to </html>). NO JavaScript at all — that will be added separately.

## BRAND DATA
Name: {name}
Niche: {niche}
Headline: {headline}
Tagline: {tagline}
Services: {', '.join(services[:6])}
CTA: {brand.get('cta_text', 'Get Started')}
Colors: accent={accent}, background={bg_a}, secondary={bg_b}
Fonts: {', '.join(fonts[:2])}

{TASTE_SKILL_RULES}

{ref_context}

## CRITICAL HTML REQUIREMENTS:
1. Output ONLY HTML with inline CSS in <style> tags — ZERO JavaScript
2. Hero section: <section id="hero-scroll-section"> with inner <div class="hero-sticky"> — height: 400vh
3. Hero headline: <h1 class="hero-headline text-scramble"> — SHORT (max 5 words), bold, editorial
4. Hero headline uses <br> for line breaks — NEVER concatenate words
5. All reveal elements use class="reveal-up" (JS will add "is-revealed" on scroll)
6. CSS must have: .reveal-up {{ opacity: 0; transform: translateY(40px); transition: opacity 0.7s, transform 0.7s; }}
7. CSS must have: .reveal-up.is-revealed {{ opacity: 1; transform: translateY(0); }}
8. Features section: id="services" data-niche-scroll="{niche}"
9. Stats use: class="count-up" data-target="500" data-suffix="+"
10. All CTAs use: class="magnetic-btn"
11. Include: <div id="scroll-progress"></div> as first child of body
12. Fully responsive: mobile-first, works at 375px and 1440px
13. overflow-x: hidden on html and body
14. Hero headline font-size: clamp(3rem, 8vw, 7rem) — never nowrap
15. Make this look like an Awwwards-winning website, NOT a generic AI site
16. Use niche-specific design choices — a restaurant site should feel like a restaurant, not a SaaS
17. Include a kinetic marquee section with brand keywords
18. Include a horizontal scroll gallery section
19. Include glassmorphism cards in at least one section
20. The hero-sticky div should have: position:sticky; top:0; height:100dvh; overflow:hidden; display:flex; align-items:center;

Output ONLY the HTML. Start with <!DOCTYPE html>. No explanation. No markdown."""

    print("[Website Builder] Calling OpenAI gpt-4.1-mini (HTML+CSS only)...")
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=16000,
            temperature=0.85
        )
        html = response.choices[0].message.content.strip()

        # Clean markdown wrappers
        html = re.sub(r'^```[a-z]*\n?', '', html)
        html = re.sub(r'\n?```$', '', html)
        html = html.strip()

        # Ensure starts with DOCTYPE
        if not html.startswith("<!DOCTYPE") and not html.startswith("<html"):
            idx = html.find("<!DOCTYPE")
            if idx == -1:
                idx = html.find("<html")
            if idx != -1:
                html = html[idx:]

        print(f"[Website Builder] AI generated {len(html):,} chars of HTML+CSS")

    except Exception as e:
        print(f"[Website Builder] AI generation failed: {e}, using fallback")
        html = _fallback_html(brand, modules_dir)

    # ── Post-processing (programmatic fixes) ──────────────────────────────
    html = fix_reveal_classes(html)
    html = fix_mobile_overflow(html)
    html = fix_hero_structure(html)
    html = fix_images_with_nano_banana(html, brand)           # Replace fake images with Nano Banana AI images
    html = fix_background_images_with_nano_banana(html, brand)  # Replace fake background images too
    html = fix_gallery_overflow(html)           # Fix horizontal gallery overflow
    html = inject_critical_overrides(html, brand)  # Aggressive !important overrides

    # Inject all JavaScript programmatically
    html = inject_scripts(html, brand, modules_dir)

    # Remove duplicate count-up AFTER script injection (so we keep our injected version)
    html = remove_duplicate_countup(html)

    # Save
    os.makedirs(output_dir, exist_ok=True)
    html_path = os.path.join(output_dir, "index.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[Website Builder] ✓ Saved: {html_path} ({len(html)//1024} KB)")
    return html_path


def _fallback_html(brand: dict, modules_dir: Path) -> str:
    """Minimal but cinematic fallback HTML (no JS — injected separately)."""
    name = brand.get('name', 'Brand')
    niche = brand.get('niche', 'business')
    accent = brand.get('colors', {}).get('accent', '#e63946')
    bg = brand.get('colors', {}).get('background', '#0d0d0d')
    bg_b = brand.get('colors', {}).get('secondary', '#1a0a2e')
    text_color = brand.get('colors', {}).get('text', '#f0f0f0')
    headline = brand.get('headline', f'Premium {niche.title()}')
    tagline = brand.get('tagline', 'Excellence in every detail')
    services = brand.get('services', ['Service 1', 'Service 2', 'Service 3'])
    cta = brand.get('cta_text', 'Get Started')

    services_html = "\n".join([
        f'<div class="service-item reveal-up" style="transition-delay:{i*0.1}s">'
        f'<span class="service-num">0{i+1}</span><h3>{s}</h3></div>'
        for i, s in enumerate(services[:6])
    ])

    marquee_items = " ".join([
        f'<span class="marquee-item">{name}</span><span class="marquee-dot">·</span>'
    ] * 8 + [
        f'<span class="marquee-item">{s}</span><span class="marquee-dot">·</span>'
        for s in (services[:3] * 4)
    ])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
:root {{
  --accent: {accent};
  --bg: {bg};
  --bg-b: {bg_b};
  --text: {text_color};
  --glass: rgba(255,255,255,0.04);
  --border: rgba(255,255,255,0.08);
}}
html, body {{ overflow-x: hidden; scroll-behavior: smooth; }}
body {{ background: var(--bg); color: var(--text); font-family: 'Geist', system-ui, sans-serif; }}

/* Scroll progress */
#scroll-progress {{
  position: fixed; top: 0; left: 0; height: 3px; width: 0%;
  background: var(--accent); z-index: 9999;
  box-shadow: 0 0 8px var(--accent);
}}

/* Nav */
nav {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 6vw;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  background: rgba(0,0,0,0.3);
  border-bottom: 1px solid var(--border);
}}
.nav-brand {{ font-size: 18px; font-weight: 700; letter-spacing: -0.02em; }}
.nav-cta {{
  padding: 10px 22px; border-radius: 100px;
  background: var(--accent); color: #fff;
  font-size: 13px; font-weight: 600; text-decoration: none;
  transition: transform 0.2s, box-shadow 0.2s;
}}
.nav-cta:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px {accent}44; }}

/* Hero */
#hero-scroll-section {{ height: 400vh; position: relative; }}
.hero-sticky {{
  position: sticky; top: 0; height: 100dvh; width: 100%;
  display: flex; align-items: center; padding-left: 8vw;
  overflow: hidden;
  background: radial-gradient(ellipse at 30% 50%, {bg_b} 0%, {bg} 60%);
}}
.hero-content {{ position: relative; z-index: 2; max-width: min(640px, 90vw); }}
.hero-eyebrow {{
  font-size: 11px; letter-spacing: 0.3em; text-transform: uppercase;
  color: rgba(255,255,255,0.4); margin-bottom: 20px;
}}
.hero-headline {{
  font-size: clamp(3rem, 8vw, 7rem);
  font-weight: 900; line-height: 1.0; letter-spacing: -0.04em;
  white-space: normal; word-wrap: break-word;
  background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.65) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; margin-bottom: 24px;
}}
.hero-sub {{
  font-size: clamp(15px, 2vw, 17px); color: rgba(255,255,255,0.5);
  line-height: 1.65; margin-bottom: 36px; max-width: 440px;
}}
.hero-cta {{
  display: inline-flex; align-items: center; gap: 10px;
  padding: 16px 32px; border-radius: 100px;
  background: var(--accent); color: #fff;
  font-size: 15px; font-weight: 600; text-decoration: none;
  transition: transform 0.2s, box-shadow 0.2s;
}}
.hero-cta:hover {{ transform: translateY(-3px); box-shadow: 0 12px 32px {accent}55; }}

/* Marquee */
.marquee-section {{
  padding: 24px 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);
  overflow: hidden; background: rgba(255,255,255,0.02);
}}
.marquee-track {{
  display: flex; gap: 48px; white-space: nowrap;
  animation: marquee 22s linear infinite;
}}
.marquee-item {{
  font-size: 13px; letter-spacing: 0.2em; text-transform: uppercase;
  color: rgba(255,255,255,0.3); flex-shrink: 0;
}}
.marquee-dot {{ color: var(--accent); flex-shrink: 0; }}
@keyframes marquee {{ from {{ transform: translateX(0); }} to {{ transform: translateX(-50%); }} }}

/* Sections */
section {{ padding: 120px 8vw; }}
.section-label {{
  font-size: 11px; letter-spacing: 0.3em; text-transform: uppercase;
  color: rgba(255,255,255,0.35); margin-bottom: 16px;
}}
.section-title {{
  font-size: clamp(2.5rem, 5vw, 4.5rem);
  font-weight: 800; letter-spacing: -0.03em; line-height: 1.1;
  margin-bottom: 48px;
}}

/* Services bento grid */
.services-bento {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: auto;
  gap: 2px; background: var(--border);
}}
.service-item {{
  background: var(--bg); padding: 40px 32px;
  transition: background 0.3s;
}}
.service-item:nth-child(1) {{ grid-column: span 2; }}
.service-item:hover {{ background: rgba(255,255,255,0.03); }}
.service-num {{
  font-size: 11px; letter-spacing: 0.2em; color: var(--accent);
  margin-bottom: 16px; display: block;
}}
.service-item h3 {{ font-size: 20px; font-weight: 600; letter-spacing: -0.02em; }}

/* Stats */
.stats-row {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 48px; margin-top: 64px;
}}
.stat-item {{ text-align: left; }}
.stat-num {{
  font-size: clamp(3rem, 6vw, 5rem); font-weight: 900;
  letter-spacing: -0.04em; color: var(--accent);
  display: block;
}}
.stat-label {{ font-size: 14px; color: rgba(255,255,255,0.4); margin-top: 8px; }}

/* Horizontal scroll gallery */
.gallery-section {{ padding: 80px 0; overflow: hidden; }}
.gallery-track {{
  display: flex; gap: 24px; padding: 0 8vw;
  overflow-x: auto; scroll-snap-type: x mandatory;
  scrollbar-width: none; cursor: grab;
}}
.gallery-track::-webkit-scrollbar {{ display: none; }}
.gallery-card {{
  flex-shrink: 0; width: 320px; height: 400px;
  border-radius: 16px; scroll-snap-align: start;
  background: linear-gradient(135deg, {bg_b} 0%, {bg} 100%);
  border: 1px solid var(--border);
  display: flex; align-items: flex-end; padding: 24px;
}}
.gallery-card-label {{ font-size: 14px; font-weight: 600; }}

/* CTA section */
.cta-section {{
  text-align: center; padding: 160px 8vw;
  background: radial-gradient(ellipse at center, {accent}15 0%, transparent 70%);
  border-top: 1px solid var(--border);
}}
.cta-section h2 {{
  font-size: clamp(2.5rem, 6vw, 5.5rem);
  font-weight: 900; letter-spacing: -0.04em; margin-bottom: 32px;
  white-space: normal;
}}
.cta-section p {{ font-size: 18px; color: rgba(255,255,255,0.5); margin-bottom: 48px; }}

/* Footer */
footer {{
  padding: 48px 8vw; border-top: 1px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 16px;
}}
footer .brand {{ font-size: 16px; font-weight: 700; }}
footer .copy {{ font-size: 13px; color: rgba(255,255,255,0.3); }}

/* Reveal animations */
.reveal-up {{ opacity: 0; transform: translateY(40px); transition: opacity 0.7s cubic-bezier(.22,1,.36,1), transform 0.7s cubic-bezier(.22,1,.36,1); }}
.reveal-up.is-revealed {{ opacity: 1; transform: translateY(0); }}
.reveal-left {{ opacity: 0; transform: translateX(-40px); transition: opacity 0.7s cubic-bezier(.22,1,.36,1), transform 0.7s cubic-bezier(.22,1,.36,1); }}
.reveal-left.is-revealed {{ opacity: 1; transform: translateX(0); }}

/* Glassmorphism */
.glass-card {{
  background: var(--glass);
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-radius: 16px; padding: 32px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
}}

@media (max-width: 768px) {{
  nav {{ padding: 16px 5vw; }}
  section {{ padding: 80px 5vw; }}
  .hero-sticky {{ padding-left: 5vw; padding-right: 5vw; }}
  .services-bento {{ grid-template-columns: 1fr; }}
  .service-item:nth-child(1) {{ grid-column: span 1; }}
  .gallery-card {{ width: 260px; height: 320px; }}
}}
</style>
</head>
<body>

<div id="scroll-progress"></div>

<nav>
  <div class="nav-brand">{name}</div>
  <a href="#services" class="nav-cta magnetic-btn">{cta}</a>
</nav>

<section id="hero-scroll-section">
  <div class="hero-sticky">
    <div class="hero-content">
      <p class="hero-eyebrow">{niche.replace('_', ' ').title()} · Premium</p>
      <h1 class="hero-headline text-scramble">{headline}</h1>
      <p class="hero-sub">{tagline}</p>
      <a href="#services" class="hero-cta magnetic-btn">{cta} <span>→</span></a>
    </div>
  </div>
</section>

<div class="marquee-section">
  <div class="marquee-track">
    {marquee_items}
    {marquee_items}
  </div>
</div>

<section id="services" data-niche-scroll="{niche}" style="background: rgba(255,255,255,0.01);">
  <p class="section-label reveal-up">What We Offer</p>
  <h2 class="section-title reveal-up">Built for<br><em style="font-style:normal;color:var(--accent)">excellence</em></h2>
  <div class="services-bento">
    {services_html}
  </div>
</section>

<section id="stats" style="background: rgba(255,255,255,0.015); border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);">
  <p class="section-label reveal-up">By the Numbers</p>
  <h2 class="section-title reveal-up">Results that<br><em style="font-style:normal;color:var(--accent)">speak</em></h2>
  <div class="stats-row">
    <div class="stat-item reveal-up">
      <span class="stat-num count-up" data-target="500" data-suffix="+">0</span>
      <p class="stat-label">Happy Clients</p>
    </div>
    <div class="stat-item reveal-up" style="transition-delay:0.1s">
      <span class="stat-num count-up" data-target="12" data-suffix=" yrs">0</span>
      <p class="stat-label">Years of Excellence</p>
    </div>
    <div class="stat-item reveal-up" style="transition-delay:0.2s">
      <span class="stat-num count-up" data-target="98" data-suffix="%">0</span>
      <p class="stat-label">Satisfaction Rate</p>
    </div>
    <div class="stat-item reveal-up" style="transition-delay:0.3s">
      <span class="stat-num count-up" data-target="50" data-suffix="k+">0</span>
      <p class="stat-label">Experiences Delivered</p>
    </div>
  </div>
</section>

<div class="gallery-section">
  <div style="padding: 0 8vw; margin-bottom: 32px;">
    <p class="section-label reveal-up">Showcase</p>
    <h2 class="section-title reveal-up" style="margin-bottom: 0;">Our<br><em style="font-style:normal;color:var(--accent)">work</em></h2>
  </div>
  <div class="gallery-track">
    {''.join([f'<div class="gallery-card"><div class="gallery-card-label">{s}</div></div>' for s in (services[:3] * 3)])}
  </div>
</div>

<section class="cta-section" id="contact">
  <p class="section-label reveal-up">Ready to Begin?</p>
  <h2 class="reveal-up">Let's create something<br><em style="font-style:normal;color:var(--accent)">extraordinary</em></h2>
  <p class="reveal-up">{tagline}</p>
  <a href="mailto:hello@brand.com" class="hero-cta magnetic-btn reveal-up">{cta} →</a>
</section>

<footer>
  <div class="brand">{name}</div>
  <div class="copy">© {name} 2025. All rights reserved.</div>
</footer>

</body>
</html>"""
