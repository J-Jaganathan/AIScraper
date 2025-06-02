#!/bin/bash
echo "▶ Installing Playwright browsers..."
playwright install chromium
echo "🚀 Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 10000
