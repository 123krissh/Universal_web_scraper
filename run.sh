#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# ----------------------------
# Step 1: Create virtual environment if it doesn't exist
# ----------------------------
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# ----------------------------
# Step 2: Activate virtual environment
# ----------------------------
echo "Activating virtual environment..."
source venv/bin/activate

# ----------------------------
# Step 3: Upgrade pip
# ----------------------------
echo "Upgrading pip..."
pip install --upgrade pip

# ----------------------------
# Step 4: Install dependencies
# ----------------------------
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# ----------------------------
# Step 5: Start FastAPI server
# ----------------------------
echo "Starting FastAPI server at http://localhost:8000 ..."
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
