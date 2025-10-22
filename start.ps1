# Quick Start Script for Hybrid RAG Platform
# Run with: ./start.ps1

Write-Host "🚀 Starting Hybrid RAG Platform..." -ForegroundColor Green

# Check if Docker is running
try {
    $dockerProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
    if (-not $dockerProcess) {
        Write-Host "❌ Docker Desktop is not running. Please start Docker Desktop first." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "⚠️  Could not check Docker status. Please ensure Docker Desktop is running." -ForegroundColor Yellow
}

# Create .env if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  Please edit .env and add your OpenAI API key!" -ForegroundColor Yellow
    Write-Host "   Set OPENAI_API_KEY=your-key-here" -ForegroundColor Yellow
    
    $response = Read-Host "Do you want to edit .env now? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        notepad .env
    }
}

# Check for OpenAI API key
$envContent = Get-Content ".env" -Raw
if ($envContent -notmatch "OPENAI_API_KEY=sk-") {
    Write-Host "⚠️  Warning: No valid OpenAI API key found in .env" -ForegroundColor Yellow
    Write-Host "   The system will work but RAG responses will be limited" -ForegroundColor Yellow
}

Write-Host "🐳 Starting services with Docker Compose..." -ForegroundColor Blue

# Use the simplified docker-compose
docker-compose -f docker-compose.simple.yml pull
docker-compose -f docker-compose.simple.yml up -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Blue
Start-Sleep 10

# Check service health
$backendHealth = try { 
    (Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5).StatusCode -eq 200 
} catch { 
    $false 
}

if ($backendHealth) {
    Write-Host "✅ Backend is healthy" -ForegroundColor Green
} else {
    Write-Host "❌ Backend is not responding. Check logs: docker-compose -f docker-compose.simple.yml logs backend" -ForegroundColor Red
}

# Run database migrations
Write-Host "📊 Running database migrations..." -ForegroundColor Blue
docker exec rag_backend poetry run alembic upgrade head

# Ask about seeding sample data
$seedResponse = Read-Host "Do you want to seed sample data? (y/n)"
if ($seedResponse -eq "y" -or $seedResponse -eq "Y") {
    Write-Host "🌱 Seeding sample data..." -ForegroundColor Blue
    docker exec rag_backend poetry run python scripts/seed_data.py
}

Write-Host ""
Write-Host "🎉 Hybrid RAG Platform is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access the application:" -ForegroundColor Cyan
Write-Host "   Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "   API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Health Check: http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "👤 Sample login credentials:" -ForegroundColor Cyan
Write-Host "   Admin: admin@example.com / admin123!" -ForegroundColor White
Write-Host "   User: user@example.com / user123!" -ForegroundColor White
Write-Host ""
Write-Host "🖥️  To start the frontend:" -ForegroundColor Cyan
Write-Host "   cd frontend" -ForegroundColor White
Write-Host "   npm install" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor White
Write-Host "   Then visit: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "   View logs: docker-compose -f docker-compose.simple.yml logs -f" -ForegroundColor White
Write-Host "   Stop services: docker-compose -f docker-compose.simple.yml down" -ForegroundColor White
Write-Host "   Reset data: docker-compose -f docker-compose.simple.yml down -v" -ForegroundColor White