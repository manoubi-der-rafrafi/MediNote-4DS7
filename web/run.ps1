# CRM Pharma - Run All Services

Write-Host "Services Starting..." -ForegroundColor Green
$webDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$managerPath = Join-Path $webDir "manager_web"
$marketingPath = Join-Path $webDir "marketing_web"
$directionPath = Join-Path $webDir "direction_web"
$shellPath = Join-Path $webDir "shell"

Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$managerPath'; npm run dev"
Write-Host "OK Manager (3001)" -ForegroundColor Green

Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$marketingPath'; npm run dev"
Write-Host "OK Marketing (3002)" -ForegroundColor Green

Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$directionPath'; npm run dev"
Write-Host "OK Direction (3003)" -ForegroundColor Green

Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$shellPath'; npm run dev"
Write-Host "OK Shell (3000)" -ForegroundColor Green

Write-Host ""
Write-Host "Visit: http://localhost:3000" -ForegroundColor Cyan
