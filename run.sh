#!/usr/bin/env bash
set -e

echo "Creating virtualenv (venv) if missing..."
python -m venv venv || true
. venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing requirements..."
pip install -r requirements.txt

echo "Installing Playwright browsers..."
python -m playwright install --with-deps

echo "Starting server at http://localhost:8000"
# Run uvicorn from project root so imports resolve properly
python -m uvicorn backend.main:app --reload --port 8000
