# OmniSearch Local Development Startup Script
# This runs the API locally without Docker

Write-Host "=== OmniSearch Local Startup ===" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install dependencies
if (-not (Test-Path ".venv\Lib\site-packages\fastapi")) {
    Write-Host "Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Set environment variables for local development
$env:WEAVIATE_URL = "http://localhost:8080"
$env:MONGODB_URL = "mongodb://localhost:27017"
$env:MONGODB_DB = "omnisearch"
$env:PYTHONUNBUFFERED = "1"
$env:LOG_LEVEL = "INFO"

Write-Host ""
Write-Host "=== Starting OmniSearch API ===" -ForegroundColor Green
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Interactive docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
