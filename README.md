# Cinematic Website Generator

> **Turn any website URL into a stunning, scroll-driven 3D cinematic experience — with AI-generated images — deployed live on Vercel in minutes.**

---

## Quick Start

### Web UI (recommended)

```bash
# Install dependencies
pip install flask requests beautifulsoup4 openai playwright
playwright install chromium

# Set your API keys
export OPENAI_API_KEY="your-openai-api-key"
export VERCEL_TOKEN="your-vercel-token"

# Start the web server
python3 app.py
# Open http://localhost:7860
```

### Command Line

```bash
python3 pipeline.py https://yourwebsite.com
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key for brand analysis and website generation |
| `VERCEL_TOKEN` | Yes | Vercel personal access token — get from vercel.com/account/tokens |
| `GOOGLE_API_KEY` | Optional | Google Gemini API key for Nano Banana image generation |
| `FAL_KEY` | Optional | fal.ai key for Seedance cinematic video generation |

---

## Pipeline Steps

| Step | What Happens |
|---|---|
| **1. Brand Analysis** | Scrapes the target URL with Playwright. Extracts brand name, colors, fonts, tagline, services, niche, and logo. |
| **2. Niche Reference** | Finds a stunning website in the same niche (e.g. restaurant → premium dining site). Extracts its design system. |
| **3. Hero Video** | Attempts to generate a Seedance cinematic hero video via fal.ai. Falls back to Three.js particle animation if no API key. |
| **4. Website Build** | Uses GPT-4.1 to generate a complete cinematic HTML site with Three.js scroll-driven hero, GSAP ScrollTrigger, and niche-specific animations. |
| **5. Nano Banana Images** | Gemini AI generates cinematic hero images tailored to your brand and uploads them to CDN. |
| **6. QA + Vision Score** | Takes screenshots (mobile, tablet, desktop). Sends to GPT-4.1 vision. Scores 10 criteria. Auto-patches HTML if score < 8/10. |
| **7. Vercel Deploy** | Deploys the final HTML to Vercel. Returns a live public URL. |

---

## File Structure

```
cinematic-pipeline/
├── app.py                         # Flask web server (UI + API)
├── pipeline.py                    # CLI pipeline runner
├── ui/
│   └── index.html                 # Web UI frontend
├── modules/
│   ├── brand_analyzer.py          # Step 1: Scrape & extract brand identity
│   ├── niche_reference.py         # Step 2: Find reference site
│   ├── video_generator.py         # Step 3: Seedance/fal.ai video generation
│   ├── website_builder.py         # Step 4: GPT-4.1 HTML generation
│   ├── image_generator.py         # Step 5: Nano Banana (Gemini) image generation
│   ├── qa_tester.py               # Step 6: AI vision QA + auto-patch
│   └── vercel_deployer.py         # Step 7: Vercel deployment
└── output/
    └── {domain}_{timestamp}/      # Generated site files
        ├── index.html             # The complete cinematic website
        ├── brand.json             # Extracted brand data
        └── pipeline-results.json  # Full pipeline results + live URL
```

---

## Web API

| Endpoint | Method | Description |
|---|---|---|
| `POST /api/generate` | POST | Start a new generation job. Body: `{"url": "https://..."}` |
| `GET /api/stream/:job_id` | GET | Server-Sent Events stream of pipeline progress |
| `GET /api/status/:job_id` | GET | Poll job status and events |
| `GET /api/jobs` | GET | List all recent jobs |
| `GET /health` | GET | Health check |

---

## Design Principles

The generator avoids generic "AI website" aesthetics:

- **No** centered hero with text over dark image
- **No** purple/neon gradients or Inter font
- **No** 3-column equal-height card layouts
- **No** generic copy ("Elevate", "Seamless", "Next-Gen")

Instead it uses asymmetric editorial layouts, niche-specific scroll animations (20+ niches), liquid glass effects, magnetic buttons, kinetic marquees, and Nano Banana AI images.

---

## Niche-Specific Scroll Animations

| Niche | Scroll Animation |
|---|---|
| Restaurant / Coffee | Steam particles rising, ingredients orbiting |
| Fitness / Gym | Muscle fibre strands tensing, energy particles surging |
| Beauty / Skincare | Liquid droplets forming, molecular structures assembling |
| Tech / SaaS | Code particles assembling into grid, circuit board traces |
| Automotive | Car exploded view with labelled parts |
| Real Estate | Building wireframe constructing floor by floor |
| Fashion | Fabric threads weaving together |
| Finance | Candlestick chart building bar by bar |
| Healthcare | DNA helix rotating and assembling |
| + 11 more | See `modules/niche_reference.py` |

---

## Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install flask requests beautifulsoup4 openai playwright
RUN playwright install --with-deps chromium
EXPOSE 7860
CMD ["python3", "app.py", "--port", "7860"]
```

```bash
docker build -t cinematic-generator .
docker run -p 7860:7860 \
  -e OPENAI_API_KEY=your-key \
  -e VERCEL_TOKEN=your-token \
  cinematic-generator
```

---

## Live Examples

| Site | URL |
|---|---|
| Nobu Restaurants | https://nobu-global-nobu-restaurants-497416.vercel.app |
| Equinox | https://equinox-497541.vercel.app |
| Aesop | https://aesop-497639.vercel.app |
| Linear | https://linear-the-system-for-product-49774.vercel.app |

---

## Credits

Built with [Three.js](https://threejs.org/), [GSAP](https://greensock.com/gsap/), [Google Gemini Nano Banana](https://ai.google.dev/), [Vercel](https://vercel.com/), and [OpenAI](https://openai.com/).
