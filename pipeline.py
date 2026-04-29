#!/usr/bin/env python3
"""
CINEMATIC WEBSITE PIPELINE
===========================
Transforms any website URL into a stunning cinematic website and deploys it live.

Usage:
    python3 pipeline.py <url>
    python3 pipeline.py https://ichiraku.com.au/

Pipeline Steps:
    1. Brand Analysis     - Extract brand identity from target URL
    2. Niche Reference    - Find + extract design system from stunning site in same niche
    3. Video Generation   - Generate Seedance cinematic hero video (or Three.js fallback)
    4. Website Build      - Generate full cinematic HTML with 3D animations
    5. QA Testing         - Test on mobile + desktop with Playwright
    6. Vercel Deploy      - Deploy live and get public URL
"""

import sys
import os
import json
import time
import shutil
from pathlib import Path
from datetime import datetime

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from brand_analyzer import analyze_brand
from niche_reference import get_design_reference
from video_generator import generate_hero_video
from website_builder import build_website
from qa_tester import run_qa
from vercel_deployer import deploy_to_vercel

OUTPUT_BASE = os.path.join(os.path.dirname(__file__), 'output')


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          CINEMATIC WEBSITE PIPELINE  v1.0                    ║
║  3D Animations · Scroll-Driven Hero · Seedance Video         ║
║  motionsites.ai · 21st.dev · Three.js · GSAP · Vercel       ║
╚══════════════════════════════════════════════════════════════╝
""")


def print_step(step: int, total: int, name: str):
    print(f"\n{'='*60}")
    print(f"  STEP {step}/{total}: {name}")
    print(f"{'='*60}")


def run_pipeline(url: str) -> dict:
    """
    Run the full pipeline for a given URL.
    Returns dict with all results including the live Vercel URL.
    """
    print_banner()
    start_time = time.time()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = url.replace('https://', '').replace('http://', '').split('/')[0].replace('.', '-')
    output_dir = os.path.join(OUTPUT_BASE, f"{domain}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    pipeline_result = {
        "url": url,
        "output_dir": output_dir,
        "timestamp": timestamp,
        "steps": {},
        "live_url": "",
        "success": False,
        "total_time": 0
    }

    # ── STEP 1: BRAND ANALYSIS ─────────────────────────────────────────────
    print_step(1, 6, "Brand Analysis")
    try:
        brand = analyze_brand(url)
        pipeline_result['steps']['brand_analysis'] = {
            "success": True,
            "name": brand.get('name'),
            "niche": brand.get('niche'),
            "colors": brand.get('colors')
        }
        print(f"  ✓ Brand: {brand.get('name')} | Niche: {brand.get('niche')}")
        print(f"  ✓ Colors: {brand.get('colors')}")
        print(f"  ✓ Fonts: {brand.get('fonts')}")
    except Exception as e:
        print(f"  ✗ Brand analysis failed: {e}")
        brand = {
            "name": domain.replace('-', ' ').title(),
            "niche": "business",
            "headline": "Premium Experience",
            "tagline": "Excellence in every detail",
            "description": "",
            "cta_text": "Get Started",
            "services": [],
            "colors": {"primary": "#1a1a1a", "secondary": "#ffffff", "accent": "#e63946", "background": "#0d0d0d", "text": "#f0f0f0"},
            "fonts": ["Geist", "Satoshi"],
            "logo_url": "",
            "social_links": {},
            "images": []
        }
        pipeline_result['steps']['brand_analysis'] = {"success": False, "error": str(e)}

    # Save brand data
    with open(os.path.join(output_dir, 'brand.json'), 'w') as f:
        json.dump(brand, f, indent=2)

    # ── STEP 2: NICHE REFERENCE ────────────────────────────────────────────
    print_step(2, 6, f"Niche Reference Extraction ({brand.get('niche', 'business')})")
    try:
        reference = get_design_reference(brand.get('niche', 'business'), output_dir)
        pipeline_result['steps']['niche_reference'] = {
            "success": True,
            "reference_url": reference.get('reference_url'),
            "has_skill_md": bool(reference.get('skill_md')),
            "has_colors": bool(reference.get('colors'))
        }
        print(f"  ✓ Reference: {reference.get('reference_url')}")
        print(f"  ✓ Design system extracted: {bool(reference.get('skill_md'))}")
    except Exception as e:
        print(f"  ✗ Niche reference failed: {e}")
        reference = {}
        pipeline_result['steps']['niche_reference'] = {"success": False, "error": str(e)}

    # ── STEP 3: VIDEO GENERATION ───────────────────────────────────────────
    print_step(3, 6, "Cinematic Hero Video Generation")
    try:
        video_result = generate_hero_video(brand, output_dir)
        pipeline_result['steps']['video_generation'] = {
            "success": True,
            "has_video": not video_result.get('fallback', True),
            "fallback": video_result.get('fallback', True),
            "prompt": video_result.get('video_prompt', '')[:100]
        }
        if video_result.get('fallback'):
            print(f"  ℹ Using Three.js animated hero (no video API key)")
        else:
            print(f"  ✓ Video generated: {video_result.get('video_path')}")
        print(f"  ✓ Prompt: {video_result.get('video_prompt', '')[:80]}...")
    except Exception as e:
        print(f"  ✗ Video generation failed: {e}")
        video_result = {"fallback": True, "video_path": "", "video_prompt": ""}
        pipeline_result['steps']['video_generation'] = {"success": False, "error": str(e)}

    # ── STEP 4: WEBSITE BUILD ──────────────────────────────────────────────
    print_step(4, 6, "Building Cinematic Website")
    try:
        html_path = build_website(brand, reference, video_result, output_dir)
        html_size = os.path.getsize(html_path) if os.path.exists(html_path) else 0
        pipeline_result['steps']['website_build'] = {
            "success": True,
            "html_path": html_path,
            "html_size_kb": round(html_size / 1024, 1)
        }
        print(f"  ✓ HTML generated: {html_path}")
        print(f"  ✓ File size: {round(html_size/1024, 1)} KB")
    except Exception as e:
        print(f"  ✗ Website build failed: {e}")
        pipeline_result['steps']['website_build'] = {"success": False, "error": str(e)}
        pipeline_result['success'] = False
        return pipeline_result

    # ── STEP 5: QA TESTING ─────────────────────────────────────────────────
    print_step(5, 6, "QA Testing (Mobile + Desktop + AI Vision)")
    try:
        qa_results = run_qa(html_path, output_dir, brand=brand, max_rewrites=2)
        pipeline_result['steps']['qa_testing'] = {
            "success": qa_results.get('passed', False),
            "vision_score": qa_results.get('final_score', 0),
            "vision_verdict": qa_results.get('vision_verdict', ''),
            "rewrites_applied": qa_results.get('rewrite_count', 0),
            "issues": qa_results.get('issues', []),
            "screenshots": qa_results.get('screenshots', {})
        }
        print(f"  ✓ QA Vision Score: {qa_results.get('final_score', 0)}/10 — {qa_results.get('vision_verdict', '')}")
        print(f"  ✓ Rewrites applied: {qa_results.get('rewrite_count', 0)}")
        if qa_results.get('issues'):
            for issue in qa_results['issues'][:3]:
                print(f"  ⚠ {issue}")
        
        # If QA found critical issues, attempt to fix
        if not qa_results.get('passed') and qa_results.get('issues'):
            print("  ℹ QA issues detected, proceeding with deployment anyway...")
    except Exception as e:
        print(f"  ✗ QA testing failed: {e}")
        pipeline_result['steps']['qa_testing'] = {"success": False, "error": str(e)}

    # ── STEP 6: VERCEL DEPLOYMENT ──────────────────────────────────────────
    print_step(6, 6, "Deploying to Vercel")
    try:
        project_name = brand.get('name', domain).lower().replace(' ', '-')[:30]
        deploy_result = deploy_to_vercel(output_dir, project_name)
        
        pipeline_result['steps']['deployment'] = deploy_result
        
        if deploy_result.get('success'):
            pipeline_result['live_url'] = deploy_result['url']
            pipeline_result['success'] = True
            print(f"  ✓ LIVE URL: {deploy_result['url']}")
        else:
            print(f"  ✗ Deployment failed: {deploy_result.get('error', 'Unknown error')}")
            pipeline_result['success'] = False
    except Exception as e:
        print(f"  ✗ Deployment exception: {e}")
        pipeline_result['steps']['deployment'] = {"success": False, "error": str(e)}

    # ── SUMMARY ────────────────────────────────────────────────────────────
    total_time = round(time.time() - start_time, 1)
    pipeline_result['total_time'] = total_time

    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE in {total_time}s")
    print(f"{'='*60}")
    print(f"  Brand:     {brand.get('name')}")
    print(f"  Niche:     {brand.get('niche')}")
    print(f"  Live URL:  {pipeline_result.get('live_url', 'N/A')}")
    print(f"  Success:   {'✓' if pipeline_result['success'] else '✗'}")
    print(f"{'='*60}\n")

    # Save full results
    results_path = os.path.join(output_dir, 'pipeline-results.json')
    with open(results_path, 'w') as f:
        json.dump(pipeline_result, f, indent=2)

    return pipeline_result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 pipeline.py <url>")
        print("Example: python3 pipeline.py https://ichiraku.com.au/")
        sys.exit(1)
    
    url = sys.argv[1]
    result = run_pipeline(url)
    
    if result['success']:
        print(f"\n🎉 SUCCESS! Live at: {result['live_url']}")
        sys.exit(0)
    else:
        print(f"\n❌ Pipeline failed. Check output at: {result['output_dir']}")
        sys.exit(1)
