#!/bin/bash
# Cinematic Website Generator — Local Setup Script
# Run: bash setup.sh

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║       Cinematic Website Generator — Setup                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 is required. Install from https://python.org"
  exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION"

# Install pip dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt -q

# Install Playwright browsers
echo "Installing Playwright browsers..."
python3 -m playwright install chromium --with-deps 2>/dev/null || \
  python3 -m playwright install chromium

echo ""
echo "✓ Dependencies installed"

# Check for API keys
echo ""
echo "─────────────────────────────────────────────────────────"
echo "API Key Setup"
echo "─────────────────────────────────────────────────────────"

if [ -z "$OPENAI_API_KEY" ]; then
  echo ""
  echo "⚠  OPENAI_API_KEY is not set."
  echo "   Get your key from: https://platform.openai.com/api-keys"
  echo "   Then run: export OPENAI_API_KEY='your-key'"
else
  echo "✓ OPENAI_API_KEY is set"
fi

if [ -z "$VERCEL_TOKEN" ]; then
  echo ""
  echo "⚠  VERCEL_TOKEN is not set."
  echo "   Get your token from: https://vercel.com/account/tokens"
  echo "   Then run: export VERCEL_TOKEN='your-token'"
else
  echo "✓ VERCEL_TOKEN is set"
fi

echo ""
echo "─────────────────────────────────────────────────────────"
echo "Ready to run!"
echo "─────────────────────────────────────────────────────────"
echo ""
echo "  Web UI:  python3 app.py"
echo "           Open http://localhost:7860"
echo ""
echo "  CLI:     python3 pipeline.py https://yourwebsite.com"
echo ""
