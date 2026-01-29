# Simple local startup for demo mode (without Weaviate/MongoDB)
# This runs a demo version that works standalone

Write-Host "=== OmniSearch Demo Mode ===" -ForegroundColor Cyan
Write-Host "Starting API in standalone demo mode..." -ForegroundColor Yellow
Write-Host ""

# Create demo config
$demoConfig = @"
# Demo mode - runs without external dependencies
DEMO_MODE=true
WEAVIATE_URL=http://localhost:8080
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=omnisearch
"@

$demoConfig | Out-File -FilePath ".env.demo" -Encoding utf8

# Install minimal dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install fastapi uvicorn pydantic python-multipart --quiet

Write-Host ""
Write-Host "=== Starting Demo Server ===" -ForegroundColor Green
Write-Host "URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
