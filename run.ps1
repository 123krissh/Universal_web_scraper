Write-Host "Starting Universal Web Scraper Setup..."

# Step 1: Create virtual environment if not exists
if (!(Test-Path -Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
} else {
    Write-Host "Virtual environment already exists."
}

# Step 2: Activate venv
Write-Host "Activating virtual environment..."
.\venv\Scripts\Activate

# Step 3: Upgrade pip
Write-Host "Upgrading pip..."
pip install --upgrade pip

# Step 4: Install dependencies
Write-Host "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Step 5: Install Playwright browsers
Write-Host "Installing Playwright browsers..."
playwright install

# Step 6: Start FastAPI server
Write-Host "Starting server at http://localhost:8000"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
