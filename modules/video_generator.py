"""
Video Generator Module
Generates cinematic hero videos using Seedance 1.0 via fal.ai API.
Falls back to generating a CSS/Three.js animated hero if video generation fails.
"""

import os
import json
import time
import requests
from openai import OpenAI


# fal.ai API key - uses free credits
FAL_API_KEY = os.environ.get("FAL_API_KEY", "")

# Niche-specific video prompts for cinematic hero sections
NICHE_VIDEO_PROMPTS = {
    "restaurant": {
        "prompt": "Cinematic close-up of steam rising from a bowl of ramen, golden broth glistening, slow motion, warm amber lighting, shallow depth of field, 4K, photorealistic, restaurant ambiance",
        "negative": "text, watermark, people, hands",
        "style": "warm, cinematic, food photography"
    },
    "fitness": {
        "prompt": "Cinematic slow motion of water droplets splashing on dark surface, dramatic studio lighting, deep blacks, high contrast, 4K, abstract motion",
        "negative": "text, watermark, faces",
        "style": "dark, dramatic, high-energy"
    },
    "beauty": {
        "prompt": "Cinematic macro shot of rose petals falling in slow motion, soft pink bokeh, luxury perfume bottle, golden hour light, 4K, elegant",
        "negative": "text, watermark, people",
        "style": "soft, luxurious, elegant"
    },
    "real_estate": {
        "prompt": "Cinematic aerial drone shot gliding over modern luxury architecture at golden hour, glass facades reflecting sunset, smooth camera movement, 4K",
        "negative": "text, watermark, people",
        "style": "architectural, luxurious, golden hour"
    },
    "tech_saas": {
        "prompt": "Cinematic abstract digital particles flowing through dark space, neon blue data streams, futuristic technology visualization, smooth motion, 4K",
        "negative": "text, watermark, faces",
        "style": "dark, futuristic, tech"
    },
    "ecommerce": {
        "prompt": "Cinematic product reveal with dramatic lighting, luxury item rotating on dark surface, light rays, smoke effects, 4K, commercial photography style",
        "negative": "text, watermark",
        "style": "commercial, luxury, dramatic"
    },
    "agency": {
        "prompt": "Cinematic abstract geometric shapes morphing in dark space, neon accent colors, smooth transitions, creative studio atmosphere, 4K",
        "negative": "text, watermark, faces",
        "style": "creative, abstract, modern"
    },
    "medical": {
        "prompt": "Cinematic abstract blue light particles flowing in clean white space, medical technology visualization, calm and precise motion, 4K",
        "negative": "text, watermark, people",
        "style": "clean, medical, trustworthy"
    },
    "hotel": {
        "prompt": "Cinematic slow pan across luxury hotel pool at twilight, still water reflections, warm ambient lighting, palm trees silhouette, 4K",
        "negative": "text, watermark, people",
        "style": "luxury, serene, aspirational"
    },
    "law": {
        "prompt": "Cinematic slow motion of scales of justice in dramatic lighting, dark marble background, gold accents, authoritative atmosphere, 4K",
        "negative": "text, watermark, people",
        "style": "authoritative, dark, prestigious"
    },
    "business": {
        "prompt": "Cinematic abstract light trails moving through dark space, smooth flowing motion, deep blacks, minimal and sophisticated, 4K",
        "negative": "text, watermark",
        "style": "minimal, sophisticated, modern"
    }
}


def generate_video_prompt_with_ai(brand: dict) -> str:
    """Use OpenAI to generate a custom video prompt based on brand data."""
    try:
        client = OpenAI()
        niche = brand.get('niche', 'business')
        name = brand.get('name', 'Brand')
        desc = brand.get('description', '')
        colors = brand.get('colors', {})
        accent = colors.get('accent', '#e63946')

        system = """You are a cinematic video director. Generate a single, vivid text-to-video prompt 
        for a hero section background video. The video should be:
        - Abstract or atmospheric (no text, no faces, no logos)
        - Cinematic quality, slow motion or smooth movement
        - 5-8 seconds loop-friendly
        - Matching the brand's niche and color palette
        - Suitable for a website hero background
        Return ONLY the prompt text, nothing else."""

        user = f"""Brand: {name}
Niche: {niche}
Description: {desc[:200]}
Accent color: {accent}

Generate a cinematic video prompt for this brand's hero section background."""

        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=200
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Video Generator] AI prompt generation failed: {e}")
        niche = brand.get('niche', 'business')
        return NICHE_VIDEO_PROMPTS.get(niche, NICHE_VIDEO_PROMPTS['business'])['prompt']


def generate_with_fal(prompt: str, output_path: str) -> str:
    """
    Generate video using fal.ai Seedance 1.0 API.
    Returns local file path or empty string if failed.
    """
    if not FAL_API_KEY:
        print("[Video Generator] No FAL_API_KEY set, skipping video generation")
        return ""

    print(f"[Video Generator] Generating video with Seedance via fal.ai...")
    headers = {
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json"
    }

    # Submit job to fal.ai Seedance 1.0 Pro Fast (text-to-video)
    payload = {
        "prompt": prompt,
        "duration": 5,
        "aspect_ratio": "16:9",
        "resolution": "720p"
    }

    try:
        # Submit request
        resp = requests.post(
            "https://queue.fal.run/fal-ai/bytedance/seedance/v1/pro/fast/text-to-video",
            headers=headers,
            json=payload,
            timeout=30
        )
        if resp.status_code not in [200, 201]:
            print(f"[Video Generator] fal.ai submit failed: {resp.status_code} {resp.text[:200]}")
            return ""

        data = resp.json()
        request_id = data.get("request_id")
        if not request_id:
            # Direct response
            video_url = data.get("video", {}).get("url", "")
            if video_url:
                return download_video(video_url, output_path)
            return ""

        print(f"[Video Generator] Job submitted: {request_id}")

        # Poll for completion
        for attempt in range(60):  # up to 5 minutes
            time.sleep(5)
            status_resp = requests.get(
                f"https://queue.fal.run/fal-ai/bytedance/seedance/v1/pro/fast/text-to-video/requests/{request_id}/status",
                headers=headers,
                timeout=15
            )
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                status = status_data.get("status", "")
                print(f"[Video Generator] Status: {status} (attempt {attempt+1})")
                if status == "COMPLETED":
                    # Get result
                    result_resp = requests.get(
                        f"https://queue.fal.run/fal-ai/bytedance/seedance/v1/pro/fast/text-to-video/requests/{request_id}",
                        headers=headers,
                        timeout=15
                    )
                    if result_resp.status_code == 200:
                        result = result_resp.json()
                        video_url = result.get("video", {}).get("url", "")
                        if video_url:
                            return download_video(video_url, output_path)
                    break
                elif status in ["FAILED", "ERROR"]:
                    print(f"[Video Generator] Job failed: {status_data}")
                    break

    except Exception as e:
        print(f"[Video Generator] fal.ai error: {e}")

    return ""


def download_video(url: str, output_path: str) -> str:
    """Download video from URL to local path."""
    try:
        print(f"[Video Generator] Downloading video from {url}")
        resp = requests.get(url, timeout=60, stream=True)
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[Video Generator] Video saved to {output_path}")
            return output_path
    except Exception as e:
        print(f"[Video Generator] Download failed: {e}")
    return ""


def generate_hero_video(brand: dict, output_dir: str) -> dict:
    """
    Main function: generate a cinematic hero video for the brand.
    Returns dict with video_path and video_prompt.
    """
    niche = brand.get('niche', 'business')
    name = brand.get('name', 'brand').lower().replace(' ', '-')
    video_path = os.path.join(output_dir, "assets", f"hero-{name}.mp4")
    os.makedirs(os.path.join(output_dir, "assets"), exist_ok=True)

    result = {
        "video_path": "",
        "video_prompt": "",
        "video_url": "",
        "fallback": True
    }

    # Generate custom prompt using AI
    prompt = generate_video_prompt_with_ai(brand)
    result["video_prompt"] = prompt
    print(f"[Video Generator] Prompt: {prompt[:100]}...")

    # Try fal.ai Seedance
    if FAL_API_KEY:
        video_path_result = generate_with_fal(prompt, video_path)
        if video_path_result:
            result["video_path"] = video_path_result
            result["fallback"] = False
            return result

    # If no API key or generation failed, use CSS/Three.js animated hero
    print("[Video Generator] Using Three.js animated hero fallback")
    result["fallback"] = True
    result["video_prompt"] = prompt
    return result


if __name__ == "__main__":
    import sys
    brand = {
        "name": "Test Restaurant",
        "niche": "restaurant",
        "description": "Premium Japanese ramen restaurant",
        "colors": {"accent": "#e63946"}
    }
    output = sys.argv[1] if len(sys.argv) > 1 else "/tmp/video-test"
    result = generate_hero_video(brand, output)
    print(json.dumps(result, indent=2))
