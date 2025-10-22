# Auto-update .env file with secure generated keys
# Run this script to automatically set secure passwords and keys

Write-Host "🔐 Generating secure keys for your RAG Platform..." -ForegroundColor Green

# Generate secure random keys
$jwtSecret = "rag_jwt_" + [System.Web.Security.Membership]::GeneratePassword(32, 8)
$jwtRefreshSecret = "rag_refresh_" + [System.Web.Security.Membership]::GeneratePassword(32, 8)
$secretKey = "rag_secret_" + [System.Web.Security.Membership]::GeneratePassword(32, 8)
$encryptionKey = [System.Web.Security.Membership]::GeneratePassword(32, 0)
$masterEncryptionKey = [System.Web.Security.Membership]::GeneratePassword(32, 0)
$dbPassword = "RagDB_" + [System.Web.Security.Membership]::GeneratePassword(16, 4)

Write-Host "✅ Generated secure keys!" -ForegroundColor Green
Write-Host ""

# Read current .env file
$envContent = Get-Content .env -Raw

# Update the keys
$envContent = $envContent -replace 'JWT_SECRET_KEY="[^"]*"', "JWT_SECRET_KEY=`"$jwtSecret`""
$envContent = $envContent -replace 'JWT_REFRESH_SECRET_KEY="[^"]*"', "JWT_REFRESH_SECRET_KEY=`"$jwtRefreshSecret`""
$envContent = $envContent -replace 'SECRET_KEY="[^"]*"', "SECRET_KEY=`"$secretKey`""
$envContent = $envContent -replace 'ENCRYPTION_KEY="[^"]*"', "ENCRYPTION_KEY=`"$encryptionKey`""
$envContent = $envContent -replace 'MASTER_ENCRYPTION_KEY="[^"]*"', "MASTER_ENCRYPTION_KEY=`"$masterEncryptionKey`""
$envContent = $envContent -replace 'your_password_here', $dbPassword

# Save updated .env
$envContent | Set-Content .env

Write-Host "🎯 Updated .env file with secure keys!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 IMPORTANT - Your Database Password:" -ForegroundColor Yellow
Write-Host "   $dbPassword" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  STILL NEEDED - Your OpenAI API Key:" -ForegroundColor Red
Write-Host "   1. Go to: https://platform.openai.com/api-keys" -ForegroundColor White
Write-Host "   2. Create a new secret key" -ForegroundColor White
Write-Host "   3. Replace 'sk-your-openai-api-key-here' in .env with your real key" -ForegroundColor White
Write-Host ""
Write-Host "🚀 After adding your OpenAI key, run: ./start-simple.ps1" -ForegroundColor Green