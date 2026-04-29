"""
Cinematic Website Generator — Web UI
Flask app with Server-Sent Events for live progress streaming.

Usage:
    python3 app.py                  # runs on port 7860
    python3 app.py --port 8080      # custom port

Required environment variables:
    OPENAI_API_KEY   — OpenAI API key
    VERCEL_TOKEN     — Vercel personal access token (vercel.com/account/tokens)

Optional:
    GOOGLE_API_KEY   — Google Gemini key for Nano Banana image generation
    FAL_KEY          — fal.ai key for Seedance hero video generation
"""

import os
import sys
import json
import time
import uuid
import threading
import traceback
from pathlib import Path
from flask import Flask, request, jsonify, Response, send_from_directory

# ── Path setup ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

app = Flask(__name__, static_folder=str(BASE_DIR / "ui"), static_url_path="")

OUTPUT_BASE = BASE_DIR / "output"
OUTPUT_BASE.mkdir(exist_ok=True)

# In-memory job store
jobs: dict = {}


# ── Pipeline runner ───────────────────────────────────────────────────────────

def run_pipeline_job(job_id: str, url: str):
    """Run the full pipeline in a background thread, streaming progress via SSE."""
    job = jobs[job_id]

    def emit(step: str, status: str, message: str, data: dict = None):
        event = {
            "step": step,
            "status": status,   # "running" | "done" | "warn" | "error"
            "message": message,
            "data": data or {},
            "ts": time.time(),
        }
        job["events"].append(event)
        job["last_step"] = step
        job["last_status"] = status

    try:
        emit("start", "done", f"Pipeline started for: {url}")

        # ── Create output directory ────────────────────────────────────────
        safe_name = (
            url.replace("https://", "").replace("http://", "")
               .replace("/", "-").replace(".", "-")
               .strip("-")[:40]
        )
        output_dir = str(OUTPUT_BASE / f"{safe_name}-{job_id[:8]}")
        os.makedirs(output_dir, exist_ok=True)
        job["output_dir"] = output_dir

        # ── Step 1: Brand Analysis ─────────────────────────────────────────
        emit("brand", "running", "Analysing brand identity, colors, and copy…")
        from modules.brand_analyzer import analyze_brand
        try:
            brand = analyze_brand(url)
            emit("brand", "done",
                 f"Brand identified: {brand.get('name', 'Unknown')} · {brand.get('niche', 'business')}",
                 {"name": brand.get("name"), "niche": brand.get("niche"),
                  "colors": brand.get("colors", {})})
        except Exception as e:
            domain = url.replace("https://", "").replace("http://", "").split("/")[0]
            brand = {
                "name": domain.replace("-", " ").title(),
                "niche": "business",
                "headline": "Premium Experience",
                "tagline": "Excellence in every detail",
                "description": "",
                "cta_text": "Get Started",
                "services": [],
                "colors": {
                    "primary": "#1a1a1a", "secondary": "#ffffff",
                    "accent": "#e63946", "background": "#0d0d0d", "text": "#f0f0f0"
                },
                "fonts": ["Geist", "Satoshi"],
                "logo_url": "",
                "social_links": {},
                "images": []
            }
            emit("brand", "warn",
                 f"Brand analysis partial — using defaults ({str(e)[:80]})")

        # Save brand data
        with open(os.path.join(output_dir, "brand.json"), "w") as f:
            json.dump(brand, f, indent=2)

        # ── Step 2: Niche Reference ────────────────────────────────────────
        emit("reference", "running", "Finding a stunning reference site in the same niche…")
        reference = {}
        try:
            from modules.niche_reference import get_design_reference
            reference = get_design_reference(brand.get("niche", "business"), output_dir)
            emit("reference", "done",
                 f"Reference found: {reference.get('reference_url', 'N/A')}",
                 {"url": reference.get("reference_url", "")})
        except Exception as e:
            emit("reference", "warn", f"Reference skipped — {str(e)[:80]}")

        # ── Step 3: Hero Video ─────────────────────────────────────────────
        emit("video", "running", "Preparing cinematic hero animation…")
        video_result = {"fallback": True, "video_path": None, "video_prompt": ""}
        try:
            from modules.video_generator import generate_hero_video
            video_result = generate_hero_video(brand, output_dir)
            if video_result.get("fallback"):
                emit("video", "done",
                     "Using Three.js animated hero (set FAL_KEY for video generation)")
            else:
                emit("video", "done", "Hero video generated",
                     {"path": video_result.get("video_path", "")})
        except Exception as e:
            emit("video", "warn",
                 f"Video skipped — using Three.js hero ({str(e)[:60]})")

        # ── Step 4: Build Website ──────────────────────────────────────────
        emit("build", "running", "Building cinematic website with Three.js + GSAP…")
        from modules.website_builder import build_website
        html_path = build_website(brand, reference, video_result, output_dir)
        size_kb = Path(html_path).stat().st_size // 1024
        emit("build", "done",
             f"Website built — {size_kb} KB",
             {"html_path": html_path, "size_kb": size_kb})

        # ── Step 5: Nano Banana Images ─────────────────────────────────────
        emit("images", "running", "Generating AI images with Nano Banana (Gemini)…")
        try:
            from modules.image_generator import fix_images_with_nano_banana
            img_result = fix_images_with_nano_banana(html_path, brand)
            count = img_result.get("replaced", 0)
            emit("images", "done",
                 f"AI images injected: {count} Nano Banana image(s)",
                 {"count": count})
        except Exception as e:
            emit("images", "warn",
                 f"Nano Banana images skipped — {str(e)[:80]}")

        # ── Step 6: QA — MANDATORY, never skipped ─────────────────────────
        # QA always runs. If Playwright is not installed it will raise a clear
        # error with install instructions rather than silently continuing.
        emit("qa", "running",
             "Running QA: desktop scroll, mobile layout, AI vision score…")

        try:
            from modules.qa_tester import run_qa
        except ImportError as e:
            raise RuntimeError(
                f"QA module failed to import: {e}\n"
                "Install dependencies: pip install playwright && playwright install chromium"
            )

        # run_qa(html_path, brand) — no output_dir, no max_rewrites kwarg
        qa_result = run_qa(html_path, brand)

        score   = qa_result.get("vision_score", 0)
        passes  = qa_result.get("passes", False)
        patched = qa_result.get("patched", False)
        issues  = qa_result.get("errors", [])

        emit(
            "qa",
            "done" if passes else "warn",
            f"QA score: {score}/10 {'✓ Passed' if passes else '⚠ Issues found'}"
            + (" — auto-patched" if patched else ""),
            {
                "score": score,
                "desktop_ok":  qa_result.get("desktop_scroll_ok"),
                "mobile_ok":   qa_result.get("mobile_scroll_ok"),
                "reveals_ok":  qa_result.get("reveals_ok"),
                "patched":     patched,
                "issues":      issues[:5],
            },
        )

        # ── Step 7: Deploy to Vercel ───────────────────────────────────────
        emit("deploy", "running", "Deploying to Vercel…")

        # Verify token is present before attempting deploy
        vercel_token = os.environ.get("VERCEL_TOKEN", "").strip()
        if not vercel_token:
            raise RuntimeError(
                "VERCEL_TOKEN is not set.\n"
                "Get a token at https://vercel.com/account/tokens\n"
                "Then run: export VERCEL_TOKEN='your-token'"
            )

        from modules.vercel_deployer import deploy_to_vercel
        project_name = brand.get("name", safe_name).lower().replace(" ", "-")[:30]
        deploy_result = deploy_to_vercel(output_dir, project_name)
        live_url = deploy_result.get("url", "")

        if live_url:
            emit("deploy", "done",
                 f"Live at: {live_url}",
                 {"url": live_url})
            job["live_url"] = live_url
            job["status"] = "complete"
            emit("complete", "done",
                 "Pipeline complete! Your cinematic site is live.",
                 {"url": live_url})
        else:
            err = deploy_result.get("error", "Unknown deployment error")
            raise RuntimeError(f"Deployment failed: {err}")

    except Exception as e:
        tb = traceback.format_exc()
        emit("error", "error",
             f"Pipeline error: {str(e)}",
             {"traceback": tb[:1000]})
        job["status"] = "error"
        job["error"] = str(e)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR / "ui"), "index.html")


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400
    if not url.startswith("http"):
        url = "https://" + url

    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = {
        "id": job_id,
        "url": url,
        "status": "running",
        "events": [],
        "live_url": None,
        "error": None,
        "output_dir": None,
        "last_step": None,
        "last_status": None,
        "created_at": time.time(),
    }

    thread = threading.Thread(
        target=run_pipeline_job, args=(job_id, url), daemon=True
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/stream/<job_id>")
def stream(job_id: str):
    """Server-Sent Events endpoint — streams pipeline progress in real time."""
    def event_generator():
        sent = 0
        while True:
            job = jobs.get(job_id)
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            events = job["events"]
            while sent < len(events):
                yield f"data: {json.dumps(events[sent])}\n\n"
                sent += 1

            if job["status"] in ("complete", "error"):
                yield f"data: {json.dumps({'step': '__end__', 'status': job['status']})}\n\n"
                break

            time.sleep(0.4)

    return Response(
        event_generator(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Connection": "keep-alive",
        },
    )


@app.route("/api/status/<job_id>")
def status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "status": job["status"],
        "live_url": job.get("live_url"),
        "error": job.get("error"),
        "events": job["events"],
    })


@app.route("/api/jobs")
def list_jobs():
    summary = []
    for job in sorted(jobs.values(), key=lambda j: j.get("created_at", 0), reverse=True):
        summary.append({
            "id": job["id"],
            "url": job["url"],
            "status": job["status"],
            "live_url": job.get("live_url"),
            "created_at": job.get("created_at"),
        })
    return jsonify(summary)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "jobs": len(jobs)})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = 7860
    for i, arg in enumerate(sys.argv[1:]):
        if arg in ("--port", "-p") and i + 2 <= len(sys.argv) - 1:
            port = int(sys.argv[i + 2])

    # Warn about missing env vars at startup
    missing = []
    if not os.environ.get("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
    if not os.environ.get("VERCEL_TOKEN"):
        missing.append("VERCEL_TOKEN")

    print(f"""
╔══════════════════════════════════════════════════════════╗
║       Cinematic Website Generator — Web UI               ║
║  Open: http://localhost:{port:<5}                           ║
╚══════════════════════════════════════════════════════════╝
""")
    if missing:
        print(f"⚠  Missing environment variables: {', '.join(missing)}")
        print("   Set them before generating sites.\n")

    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
