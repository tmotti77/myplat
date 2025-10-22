# Simple Start Script for Hybrid RAG Platform
Write-Host "Starting Hybrid RAG Platform..." -ForegroundColor Green

# Create .env if needed
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env and add your OpenAI API key!" -ForegroundColor Yellow
    notepad .env
    Read-Host "Press Enter after saving .env file"
}

# Start services
Write-Host "Starting Docker services..." -ForegroundColor Blue
docker-compose -f docker-compose.simple.yml up -d

# Wait for startup
Write-Host "Waiting for services to start..." -ForegroundColor Blue
Start-Sleep 15

# Run migrations
Write-Host "Running database migrations..." -ForegroundColor Blue
docker exec rag_backend poetry run alembic upgrade head

# Seed data
$seed = Read-Host "Seed sample data? (y/n)"
if ($seed -eq "y") {
    Write-Host "Seeding sample data..." -ForegroundColor Blue
    docker exec rag_backend poetry run python scripts/seed_data.py
}

Write-Host ""
Write-Host "Platform is ready!" -ForegroundColor Green
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Login: admin@example.com / admin123!" -ForegroundColor Yellow
Write-Host ""
Write-Host "For frontend:" -ForegroundColor Cyan
Write-Host "  cd frontend" -ForegroundColor White
Write-Host "  npm install" -ForegroundColor White
Write-Host "  npm run dev" -ForegroundColor White