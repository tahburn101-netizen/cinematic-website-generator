"""
Brand Analyzer Module
Scrapes any website URL and extracts brand identity:
- Business name, niche/category
- Color palette (primary, secondary, accent, background, text)
- Typography (fonts used)
- Key copy (headline, tagline, services, CTA, contact info)
- Logo URL
- Social links
"""

import re
import json
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from colorthief import ColorThief
from io import BytesIO
from playwright.sync_api import sync_playwright


def hex_from_rgb(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def detect_niche(text, url):
    """Detect the business niche from content and URL."""
    text_lower = text.lower()
    url_lower = url.lower()
    combined = text_lower + " " + url_lower

    niches = {
        "restaurant": ["restaurant", "menu", "food", "dining", "eat", "cuisine", "chef", "bistro", "cafe", "ramen", "sushi", "pizza", "burger", "bar", "grill", "bakery", "coffee"],
        "fitness": ["gym", "fitness", "workout", "training", "personal trainer", "yoga", "pilates", "crossfit", "health", "wellness"],
        "beauty": ["salon", "beauty", "spa", "hair", "nail", "makeup", "skincare", "barber", "aesthetic"],
        "real_estate": ["real estate", "property", "homes", "realty", "mortgage", "apartment", "rental", "housing"],
        "tech_saas": ["software", "saas", "app", "platform", "dashboard", "api", "developer", "startup", "tech", "ai", "automation"],
        "ecommerce": ["shop", "store", "buy", "cart", "product", "ecommerce", "fashion", "clothing", "jewelry"],
        "agency": ["agency", "studio", "creative", "design", "marketing", "branding", "digital", "consulting"],
        "medical": ["clinic", "medical", "health", "doctor", "dental", "therapy", "hospital", "care"],
        "hotel": ["hotel", "resort", "accommodation", "stay", "booking", "luxury", "suite", "inn"],
        "law": ["law", "legal", "attorney", "lawyer", "firm", "counsel"],
    }

    scores = {}
    for niche, keywords in niches.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[niche] = score

    if scores:
        return max(scores, key=scores.get)
    return "business"


def extract_fonts_from_css(css_text):
    """Extract font family names from CSS."""
    fonts = []
    # Match font-family declarations
    matches = re.findall(r'font-family\s*:\s*([^;}{]+)', css_text, re.IGNORECASE)
    for m in matches:
        # Clean up the font name
        parts = m.split(',')
        for p in parts:
            p = p.strip().strip('"\'')
            if p and p.lower() not in ['serif', 'sans-serif', 'monospace', 'cursive', 'fantasy', 'inherit', 'initial']:
                fonts.append(p)
    # Also match @import Google Fonts
    gf_matches = re.findall(r'family=([A-Za-z+]+)', css_text)
    for gf in gf_matches:
        fonts.append(gf.replace('+', ' '))
    return list(dict.fromkeys(fonts))[:5]  # unique, top 5


def extract_colors_from_css(css_text):
    """Extract color values from CSS."""
    colors = []
    # hex colors
    hex_colors = re.findall(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b', css_text)
    for h in hex_colors:
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        colors.append('#' + h.lower())
    # rgb colors
    rgb_colors = re.findall(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', css_text)
    for r, g, b in rgb_colors:
        colors.append(hex_from_rgb((int(r), int(g), int(b))))
    return list(dict.fromkeys(colors))


def get_dominant_colors_from_image(img_url):
    """Get dominant colors from an image (logo/hero)."""
    try:
        resp = requests.get(img_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            ct = ColorThief(BytesIO(resp.content))
            palette = ct.get_palette(color_count=5, quality=1)
            return [hex_from_rgb(c) for c in palette]
    except Exception:
        pass
    return []


def analyze_brand(url: str) -> dict:
    """
    Main function: analyze a website and return brand data dict.
    """
    print(f"[Brand Analyzer] Analyzing: {url}")
    brand = {
        "url": url,
        "name": "",
        "niche": "",
        "tagline": "",
        "headline": "",
        "description": "",
        "cta_text": "",
        "services": [],
        "contact": {},
        "colors": {
            "primary": "#1a1a1a",
            "secondary": "#ffffff",
            "accent": "#e63946",
            "background": "#0d0d0d",
            "text": "#f0f0f0"
        },
        "fonts": ["Geist", "Satoshi"],
        "logo_url": "",
        "social_links": {},
        "css_colors": [],
        "images": []
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2500)
            # Also try to get text via JS evaluation for better extraction
            html = page.content()
            # Extract visible text via JS
            try:
                page_title = page.title()
                page_text = page.evaluate("() => document.body.innerText")
            except Exception:
                page_title = ""
                page_text = ""
            browser.close()
    except Exception as e:
        print(f"[Brand Analyzer] Playwright failed, falling back to requests: {e}")
        try:
            resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            html = resp.text
        except Exception as e2:
            print(f"[Brand Analyzer] requests also failed: {e2}")
            return brand

    soup = BeautifulSoup(html, 'lxml')
    base_url = url.rstrip('/')
    # page_text and page_title are set in the try block above
    # Use locals() to safely access them
    _locals = locals()
    page_text = _locals.get('page_text', '')
    page_title = _locals.get('page_title', '')

    # --- Business Name ---
    og_site = soup.find('meta', property='og:site_name')
    og_title = soup.find('meta', property='og:title')
    title_tag = soup.find('title')
    if og_site and og_site.get('content'):
        brand['name'] = og_site['content'].strip()
    elif og_title and og_title.get('content'):
        brand['name'] = og_title['content'].split('|')[0].split('-')[0].strip()
    elif title_tag:
        brand['name'] = title_tag.text.split('|')[0].split('-')[0].strip()
    elif page_title:
        brand['name'] = page_title.split('|')[0].split('-')[0].strip()

    # --- Description / Tagline ---
    og_desc = soup.find('meta', property='og:description')
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if og_desc and og_desc.get('content'):
        brand['description'] = og_desc['content'].strip()[:300]
    elif meta_desc and meta_desc.get('content'):
        brand['description'] = meta_desc['content'].strip()[:300]

    # --- Headline from H1 ---
    h1 = soup.find('h1')
    if h1:
        brand['headline'] = h1.get_text(strip=True)[:120]

    # --- Tagline from H2 ---
    h2 = soup.find('h2')
    if h2:
        brand['tagline'] = h2.get_text(strip=True)[:120]

    # --- CTA buttons ---
    cta_candidates = soup.find_all(['a', 'button'], string=re.compile(
        r'(book|reserve|order|get started|contact|call|visit|try|sign up|learn more|explore|shop)', re.I))
    if cta_candidates:
        brand['cta_text'] = cta_candidates[0].get_text(strip=True)

    # --- Services from nav/lists ---
    nav = soup.find('nav')
    if nav:
        links = nav.find_all('a')
        services = [a.get_text(strip=True) for a in links if a.get_text(strip=True) and len(a.get_text(strip=True)) < 40]
        brand['services'] = services[:8]

    # --- Logo ---
    logo_candidates = soup.find_all('img', src=re.compile(r'logo', re.I))
    if not logo_candidates:
        logo_candidates = soup.find_all('img', alt=re.compile(r'logo', re.I))
    if logo_candidates:
        logo_src = logo_candidates[0].get('src', '')
        if logo_src:
            brand['logo_url'] = urljoin(base_url, logo_src)

    # --- Contact info ---
    phone_match = re.search(r'(\+?[\d\s\-\(\)]{7,15})', soup.get_text())
    if phone_match:
        brand['contact']['phone'] = phone_match.group(1).strip()
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', soup.get_text())
    if email_match:
        brand['contact']['email'] = email_match.group(0)

    # --- Social links ---
    social_patterns = {'instagram': 'instagram.com', 'facebook': 'facebook.com',
                       'twitter': 'twitter.com', 'tiktok': 'tiktok.com', 'linkedin': 'linkedin.com'}
    for a in soup.find_all('a', href=True):
        href = a['href']
        for platform, domain in social_patterns.items():
            if domain in href:
                brand['social_links'][platform] = href

    # --- Extract CSS for colors and fonts ---
    all_css = ""
    style_tags = soup.find_all('style')
    for st in style_tags:
        all_css += st.string or ""

    # Fetch linked CSS files
    link_tags = soup.find_all('link', rel='stylesheet')
    for lt in link_tags[:5]:
        href = lt.get('href', '')
        if href:
            css_url = urljoin(base_url, href)
            try:
                r = requests.get(css_url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
                all_css += r.text
            except Exception:
                pass

    if all_css:
        css_colors = extract_colors_from_css(all_css)
        brand['css_colors'] = css_colors[:20]
        fonts = extract_fonts_from_css(all_css)
        if fonts:
            brand['fonts'] = fonts[:3]

    # --- Determine color palette from CSS ---
    if brand['css_colors']:
        # Filter out white/near-white and black/near-black for accent
        filtered = [c for c in brand['css_colors'] if c not in ['#ffffff', '#fff', '#000000', '#000']]
        if filtered:
            brand['colors']['accent'] = filtered[0]
        # Most common dark color as background
        dark = [c for c in brand['css_colors'] if all(int(c[i:i+2], 16) < 60 for i in (1, 3, 5)) if len(c) == 7]
        if dark:
            brand['colors']['background'] = dark[0]
        # Most common light color as text
        light = [c for c in brand['css_colors'] if all(int(c[i:i+2], 16) > 200 for i in (1, 3, 5)) if len(c) == 7]
        if light:
            brand['colors']['text'] = light[0]

    # --- Images ---
    imgs = soup.find_all('img', src=True)
    img_urls = []
    for img in imgs[:10]:
        src = img.get('src', '')
        if src and not src.startswith('data:'):
            img_urls.append(urljoin(base_url, src))
    brand['images'] = img_urls

    # --- Niche detection ---
    full_text = soup.get_text(separator=' ', strip=True)
    if page_text:
        full_text = full_text + ' ' + page_text
    brand['niche'] = detect_niche(full_text, url)

    # --- AI fallback: if name/niche are missing or page was blocked, use OpenAI to infer from URL ---
    blocked_signals = ['access denied', 'enable javascript', 'checking your browser', 'just a moment', '403 forbidden', 'captcha']
    page_lower = (page_text or '').lower()
    is_blocked = any(s in page_lower for s in blocked_signals) or len(page_text or '') < 200

    if is_blocked or not brand['name'] or brand['niche'] == 'business':
        print(f"[Brand Analyzer] Page blocked or low-quality data — using AI fallback for: {url}")
        try:
            from openai import OpenAI
            client = OpenAI()
            domain = urlparse(url).netloc.replace('www.', '')
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{
                    "role": "user",
                    "content": f"""Given the website URL domain '{domain}', infer the brand identity.
Return ONLY a JSON object with these exact keys:
- name: the brand/company name (string)
- niche: one of: restaurant, fitness, beauty, real_estate, tech_saas, ecommerce, agency, medical, hotel, law, automotive, finance, education, entertainment, business
- tagline: a realistic tagline for this brand (string, max 10 words)
- headline: a short punchy headline for the hero section (max 5 words, ALL CAPS)
- services: array of 4-6 realistic service/product names for this brand
- cta_text: a realistic CTA button text (2-4 words)
- accent_color: a hex color that fits this brand's identity
- bg_color: a dark hex color for the background

Return ONLY the JSON, no explanation."""
                }],
                max_tokens=400,
                temperature=0.3
            )
            ai_text = resp.choices[0].message.content.strip()
            # Clean markdown
            ai_text = re.sub(r'^```[a-z]*\n?', '', ai_text)
            ai_text = re.sub(r'\n?```$', '', ai_text)
            ai_data = json.loads(ai_text)

            if not brand['name'] or is_blocked:
                brand['name'] = ai_data.get('name', brand['name'])
            if brand['niche'] == 'business' or is_blocked:
                brand['niche'] = ai_data.get('niche', brand['niche'])
            if not brand['tagline']:
                brand['tagline'] = ai_data.get('tagline', '')
            if not brand['headline']:
                brand['headline'] = ai_data.get('headline', '')
            if not brand['services']:
                brand['services'] = ai_data.get('services', [])
            if not brand['cta_text']:
                brand['cta_text'] = ai_data.get('cta_text', 'Get Started')
            if ai_data.get('accent_color'):
                brand['colors']['accent'] = ai_data['accent_color']
            if ai_data.get('bg_color'):
                brand['colors']['background'] = ai_data['bg_color']

            print(f"[Brand Analyzer] AI fallback: name='{brand['name']}', niche='{brand['niche']}'")
        except Exception as e:
            print(f"[Brand Analyzer] AI fallback failed: {e}")
            # Last resort: parse domain name
            domain = urlparse(url).netloc.replace('www.', '').split('.')[0]
            if not brand['name']:
                brand['name'] = domain.title()

    print(f"[Brand Analyzer] Done. Name: '{brand['name']}', Niche: '{brand['niche']}'")
    return brand


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://ichiraku.com.au/"
    result = analyze_brand(url)
    print(json.dumps(result, indent=2))
