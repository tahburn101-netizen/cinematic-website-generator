"""
Nano Banana Image Generator Module
===================================
Generates AI images for cinematic websites using Nano Banana (Google Gemini image generation).

Architecture:
- Uses the google-genai SDK with a Gemini API key for on-demand generation
- Falls back to a pre-generated CDN image cache for known niches
- Falls back to Unsplash if all else fails
- Images are uploaded to Manus CDN via manus-upload-file for permanent public URLs

Usage in pipeline:
    from modules.image_generator import generate_site_images, replace_images_in_html
"""

import os
import re
import json
import time
import hashlib
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Pre-generated Nano Banana image cache
# These were generated using Nano Banana (Gemini image generation)
# and uploaded to Manus CDN for permanent public access
# ─────────────────────────────────────────────
NANO_BANANA_CACHE = {
    # Nobu / Restaurant niche
    "nobu_hero":      "https://files.manuscdn.com/user_upload_by_module/session_file/310519663612569797/DxewbjbCemTHLqSL.jpg",
    "nobu_food":      "https://files.manuscdn.com/user_upload_by_module/session_file/310519663612569797/ZyruOymGyiNTMciD.jpg",
    "nobu_sushi":     "https://files.manuscdn.com/user_upload_by_module/session_file/310519663612569797/KIygYBYIyIiiZDtl.jpg",
    # Equinox / Fitness niche
    "equinox_hero":   "https://files.manuscdn.com/user_upload_by_module/session_file/310519663612569797/GzlgFhEHeqLncXFh.jpg",
    "equinox_pool":   "https://files.manuscdn.com/user_upload_by_module/session_file/310519663612569797/KaAIfSOUrsAlSfgl.jpg",
    "equinox_weights":"https://files.manuscdn.com/user_upload_by_module/session_file/310519663612569797/KkNcpmeIgBTGWNVW.jpg",
    # Aesop / Beauty niche
    "aesop_hero":     "https://files.manuscdn.com/user_upload_by_module/session_file/310519663612569797/hUojydxMPSnMypNs.jpg",
    "aesop_products": "https://files.manuscdn.com/user_upload_by_module/session_file/310519663612569797/xLzBXnuwzEhDlFTc.jpg",
    "aesop_texture":  "https://files.manuscdn.com/user_upload_by_module/session_file/310519663612569797/uaZTLeorhrHGbLaf.jpg",
    # Linear / Tech SaaS niche
    "linear_hero":    "https://files.manuscdn.com/user_upload_by_module/session_file/310519663612569797/ELaMbxBGpnpCmFOg.jpg",
    "linear_abstract":"https://files.manuscdn.com/user_upload_by_module/session_file/310519663612569797/cJbDmkSiGFXvkMxP.jpg",
    "linear_workspace":"https://files.manuscdn.com/user_upload_by_module/session_file/310519663612569797/PYnJJdTASDhJXBUy.jpg",
}

# ─────────────────────────────────────────────
# Niche → Nano Banana image sets
# Maps niche keywords to pre-generated AI image URLs
# ─────────────────────────────────────────────
NICHE_IMAGE_SETS = {
    "restaurant": [
        NANO_BANANA_CACHE["nobu_hero"],
        NANO_BANANA_CACHE["nobu_food"],
        NANO_BANANA_CACHE["nobu_sushi"],
    ],
    "fitness": [
        NANO_BANANA_CACHE["equinox_hero"],
        NANO_BANANA_CACHE["equinox_pool"],
        NANO_BANANA_CACHE["equinox_weights"],
    ],
    "beauty": [
        NANO_BANANA_CACHE["aesop_hero"],
        NANO_BANANA_CACHE["aesop_products"],
        NANO_BANANA_CACHE["aesop_texture"],
    ],
    "tech_saas": [
        NANO_BANANA_CACHE["linear_hero"],
        NANO_BANANA_CACHE["linear_abstract"],
        NANO_BANANA_CACHE["linear_workspace"],
    ],
    # Fallback sets using cross-niche images
    "hotel": [
        NANO_BANANA_CACHE["equinox_pool"],
        NANO_BANANA_CACHE["nobu_hero"],
        NANO_BANANA_CACHE["aesop_hero"],
    ],
    "default": [
        NANO_BANANA_CACHE["nobu_hero"],
        NANO_BANANA_CACHE["aesop_products"],
        NANO_BANANA_CACHE["linear_abstract"],
    ],
}

# ─────────────────────────────────────────────
# On-demand generation using google-genai SDK
# ─────────────────────────────────────────────

def _try_gemini_generate(prompt: str, output_path: str, api_key: str) -> bool:
    """Try to generate an image using the Gemini API (Nano Banana)."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"]
            )
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                return True
    except Exception as e:
        logger.warning(f"Gemini generation failed: {e}")
    return False


def _upload_to_cdn(local_path: str) -> Optional[str]:
    """Upload a local image file to Manus CDN and return the public URL."""
    try:
        result = subprocess.run(
            ["manus-upload-file", local_path],
            capture_output=True, text=True, timeout=120
        )
        match = re.search(r"CDN URL: (https://\S+)", result.stdout)
        if match:
            return match.group(1)
        logger.warning(f"Upload failed: {result.stdout} {result.stderr}")
    except Exception as e:
        logger.warning(f"CDN upload failed: {e}")
    return None


def generate_image_for_niche(
    niche: str,
    brand_name: str,
    description: str,
    index: int = 0,
    gemini_api_key: str = ""
) -> str:
    """
    Generate or retrieve an AI image for the given niche.
    
    Returns a public CDN URL for the image.
    Priority:
    1. On-demand Gemini generation (if API key available)
    2. Pre-generated Nano Banana cache (niche-matched)
    3. Unsplash fallback
    """
    # Normalize niche
    niche_lower = niche.lower()
    
    # Determine image set
    if any(k in niche_lower for k in ["restaurant", "food", "cafe", "coffee", "dining", "nobu"]):
        image_set = NICHE_IMAGE_SETS["restaurant"]
    elif any(k in niche_lower for k in ["fitness", "gym", "sport", "equinox", "workout"]):
        image_set = NICHE_IMAGE_SETS["fitness"]
    elif any(k in niche_lower for k in ["beauty", "skin", "cosmetic", "aesop", "apothecary", "skincare"]):
        image_set = NICHE_IMAGE_SETS["beauty"]
    elif any(k in niche_lower for k in ["tech", "saas", "software", "app", "linear", "startup"]):
        image_set = NICHE_IMAGE_SETS["tech_saas"]
    elif any(k in niche_lower for k in ["hotel", "luxury", "hospitality", "resort"]):
        image_set = NICHE_IMAGE_SETS["hotel"]
    else:
        image_set = NICHE_IMAGE_SETS["default"]

    # Try on-demand Gemini generation if API key is provided
    if gemini_api_key:
        prompt = (
            f"Cinematic, editorial photography for {brand_name} brand. "
            f"{description}. "
            f"Ultra high quality, 8K, photorealistic, dramatic lighting, no text, no watermarks."
        )
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
        
        if _try_gemini_generate(prompt, tmp_path, gemini_api_key):
            cdn_url = _upload_to_cdn(tmp_path)
            if cdn_url:
                logger.info(f"Generated Nano Banana image: {cdn_url}")
                return cdn_url

    # Fall back to pre-generated cache
    url = image_set[index % len(image_set)]
    logger.info(f"Using cached Nano Banana image [{niche}][{index}]: {url}")
    return url


def get_niche_images(niche: str, brand_name: str = "", count: int = 5) -> list:
    """
    Get a list of AI-generated image URLs for the given niche.
    Returns `count` URLs, cycling through the available set.
    """
    urls = []
    for i in range(count):
        url = generate_image_for_niche(niche, brand_name, f"Image {i+1} for {niche}", index=i)
        urls.append(url)
    return urls


# ─────────────────────────────────────────────
# HTML post-processing: replace broken images
# ─────────────────────────────────────────────

def fix_images_with_nano_banana(html: str, brand: dict) -> str:
    """
    Replace broken/fake image URLs in HTML with Nano Banana AI-generated images.
    
    This replaces the old Unsplash-based fix_broken_images() function.
    """
    niche = brand.get("niche", "default")
    brand_name = brand.get("name", "Brand")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")

    img_idx = [0]

    def replace_img_src(match):
        full_tag = match.group(0)
        src = match.group(1)

        # Determine if this src should be replaced with a Nano Banana image
        # Replace: Unsplash, picsum, placeholder, fake CDN URLs, broken URLs
        # Keep: data URIs, Manus CDN, SVG logos, actual brand assets
        is_replaceable = (
            not src.startswith("data:") and
            not src.startswith("https://files.manuscdn.com") and
            not src.endswith(".svg") and
            not "logo" in src.lower() and
            not "icon" in src.lower() and
            (
                src.startswith("https://images.unsplash.com") or
                src.startswith("https://picsum.photos") or
                "placeholder" in src.lower() or
                "example.com" in src or
                src in ("", "#") or
                re.search(r"via\.placeholder", src) is not None or
                re.search(r"assets\.[a-z]+\.(com|net|org)/images", src) is not None or
                # Replace broken CDN patterns the AI hallucinates
                re.search(r"cdn\.(nobu|equinox|aesop|linear)\.(com|app)", src) is not None or
                re.search(r"(nobu|equinox|aesop|linear)\.app/assets", src) is not None
            )
        )
        is_fake = is_replaceable

        if is_fake:
            real_src = generate_image_for_niche(
                niche=niche,
                brand_name=brand_name,
                description=f"Section image {img_idx[0]+1}",
                index=img_idx[0],
                gemini_api_key=gemini_key
            )
            img_idx[0] += 1
            return full_tag.replace(src, real_src)
        return full_tag

    html = re.sub(r'<img[^>]+src=["\']([^"\']*)["\'][^>]*>', replace_img_src, html)
    return html


# ─────────────────────────────────────────────
# Background image CSS replacement
# ─────────────────────────────────────────────

def fix_background_images_with_nano_banana(html: str, brand: dict) -> str:
    """
    Replace broken background-image: url(...) CSS values with Nano Banana images.
    """
    niche = brand.get("niche", "default")
    brand_name = brand.get("name", "Brand")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")

    bg_idx = [0]

    def replace_bg_url(match):
        full = match.group(0)
        url = match.group(1)

        is_fake = (
            not url.startswith("data:") and
            not url.startswith("https://files.manuscdn.com") and
            not url.startswith("https://images.unsplash.com") and
            (
                "placeholder" in url.lower() or
                "example.com" in url or
                url in ("", "#") or
                re.search(r"assets\.[a-z]+\.(com|net|org)", url) is not None
            )
        )

        if is_fake:
            real_url = generate_image_for_niche(
                niche=niche,
                brand_name=brand_name,
                description=f"Background image {bg_idx[0]+1}",
                index=bg_idx[0],
                gemini_api_key=gemini_key
            )
            bg_idx[0] += 1
            return full.replace(url, real_url)
        return full

    html = re.sub(
        r'background-image\s*:\s*url\(["\']?([^"\')\s]+)["\']?\)',
        replace_bg_url,
        html
    )
    return html


if __name__ == "__main__":
    # Quick test
    print("Testing Nano Banana image generator...")
    brand = {"niche": "restaurant", "name": "Nobu"}
    urls = get_niche_images("restaurant", "Nobu", count=3)
    for i, url in enumerate(urls):
        print(f"  Image {i+1}: {url}")
    print("Done!")
