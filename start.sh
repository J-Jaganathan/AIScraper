#!/bin/bash

echo "🔧 Setting up environment..."

# Set Playwright environment variables
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.cache/ms-playwright
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🎭 Installing Playwright browsers..."
playwright install chromium --with-deps

echo "🧪 Testing Playwright installation..."
python -c "from playwright.sync_api import sync_playwright; print('Playwright imported successfully')"

echo "🚀 Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}