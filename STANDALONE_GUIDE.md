# Cinematic Website Generator — Standalone Usage Guide

This guide explains how to run the Cinematic Website Generator locally on your own machine (Mac, Windows, or Linux) without requiring the Manus AI platform.

The pipeline is fully automated and uses the OpenAI API, Playwright, and Vercel CLI to scrape a URL, generate a stunning 3D scroll-driven website, run AI vision QA on the result, and deploy it to a public URL.

## 1. Prerequisites

Before you begin, ensure you have the following installed on your machine:

- **Python 3.10 or higher**: Download from [python.org](https://www.python.org/downloads/)
- **Git**: Download from [git-scm.com](https://git-scm.com/)
- **Node.js** (optional but recommended for Vercel CLI): Download from [nodejs.org](https://nodejs.org/)

## 2. Clone the Repository

Open your terminal or command prompt and clone the repository you just created:

```bash
git clone https://github.com/tahburn101-netizen/cinematic-website-generator.git
cd cinematic-website-generator
```

## 3. Install Dependencies

The project includes a setup script for macOS/Linux users, but you can also install everything manually.

**Option A: Using the setup script (Mac/Linux)**
```bash
bash setup.sh
```

**Option B: Manual installation (Windows/Mac/Linux)**
```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers (required for brand scraping and QA testing)
playwright install chromium
```

## 4. Set Up API Keys

The pipeline requires two API keys to function. These must be set as environment variables.

### Getting the keys:

1. **OpenAI API Key**: Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys), create an account if you don't have one, and generate a new secret key. You will need a few cents of credit on your account (the pipeline uses GPT-4o-mini which is very cheap).
2. **Vercel Token**: Go to [vercel.com/account/tokens](https://vercel.com/account/tokens), create a free account, and generate a new token (name it "cinematic-generator").

### Setting the keys:

**On macOS / Linux:**
```bash
export OPENAI_API_KEY="sk-your-openai-key-here"
export VERCEL_TOKEN="your-vercel-token-here"
```

**On Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY="sk-your-openai-key-here"
set VERCEL_TOKEN="your-vercel-token-here"
```

**On Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-your-openai-key-here"
$env:VERCEL_TOKEN="your-vercel-token-here"
```

## 5. Run the Generator

You have two ways to run the generator: via the Web UI or via the Command Line.

### Method 1: Web UI (Recommended)

The Web UI provides a beautiful interface with real-time progress streaming.

```bash
python app.py
```

1. Open your browser and navigate to `http://localhost:7860`.
2. Paste any website URL (e.g., `https://www.apple.com`).
3. Click **Generate**.
4. Watch the pipeline run through all 7 steps.
5. When finished, click the link to view your live, public Vercel site.

### Method 2: Command Line

If you prefer to run it headlessly in the terminal:

```bash
python pipeline.py https://www.apple.com
```

The terminal will output the progress of each step. Once complete, the final public Vercel URL will be printed at the bottom.

## 6. How the Pipeline Works

When you submit a URL, the pipeline executes the following sequence:

1. **Brand Analysis**: Playwright opens a headless browser, navigates to the URL, and extracts the brand's primary colors, fonts, tagline, services, and logo.
2. **Niche Reference**: The system determines the brand's industry (e.g., tech, fitness, restaurant) and selects an appropriate 3D scroll animation pattern (e.g., code particles for tech, steam particles for coffee).
3. **Hero Generation**: It prepares the configuration for the Three.js WebGL hero canvas.
4. **Website Build**: GPT generates a complete, single-file HTML cinematic website utilizing Three.js and GSAP ScrollTrigger.
5. **Image Generation**: If a Google Gemini key is provided (`GOOGLE_API_KEY`), it generates Nano Banana AI images and injects them into the site.
6. **QA Testing**: Playwright renders the generated HTML at desktop and mobile resolutions. It scrolls the page, takes screenshots, and sends them to GPT Vision. If the score is below 7/10, or if mobile overflow is detected, the AI automatically patches the HTML code.
7. **Vercel Deployment**: The final, QA-approved HTML is deployed to Vercel via their REST API. A permanent, public alias URL is returned.

## Troubleshooting

- **"Vercel deployment failed"**: Ensure your `VERCEL_TOKEN` is correct and hasn't expired.
- **"Playwright module not found"**: You likely forgot to run `playwright install chromium`.
- **"OpenAI API Error"**: Ensure your `OPENAI_API_KEY` is correct and your account has billing set up (even $5 is enough for hundreds of generations).
- **Sites look generic**: The system is specifically prompted to avoid generic "AI website" aesthetics. If the output looks too simple, the QA module may have failed to capture screenshots properly. Ensure you are running Python 3.10+ and have sufficient RAM.

## Advanced Configuration

You can customize the pipeline by editing the following files:
- `modules/website_builder.py`: Modify the GPT prompts to change the overall design style.
- `modules/qa_tester.py`: Adjust the strictness of the QA scoring (e.g., change the required passing score from 7 to 8).
- `modules/niche_reference.py`: Add new industries and custom scroll animation patterns.
