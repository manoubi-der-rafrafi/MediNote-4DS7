@echo off
REM CRM Pharma — Run All Web Applications on Single Port
REM Launches unified shell + 3 dashboards

echo ============================================
echo CRM Pharma — Starting Unified Dashboard
echo ============================================
echo.

REM Get current directory
cd /d "%~dp0"

REM Check if npm exists
npm -v >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm not found. Please install Node.js 18+
    exit /b 1
)

REM Install shell if needed
echo [1/4] Installing Shell dependencies...
cd "%~dp0shell"
if not exist "node_modules" (
    call npm install
)

REM Start all services
echo.
echo [2/4] Starting Manager Dashboard on port 3001...
cd "%~dp0manager_web"
start "CRM - Manager" cmd /k "npm run dev"

echo [3/4] Starting Marketing Dashboard on port 3002...
cd "%~dp0marketing_web"
start "CRM - Marketing" cmd /k "npm run dev"

echo [4/4] Starting Direction Dashboard on port 3003...
cd "%~dp0direction_web"
start "CRM - Direction" cmd /k "npm run dev"

echo.
echo Starting Shell (Unified Interface) on port 3000...
cd "%~dp0shell"
start "CRM - Shell" cmd /k "npm run dev"

echo.
echo ============================================
echo All services starting...
echo ============================================
echo.
echo MAIN URL (Unified Interface):
echo   http://localhost:3000
echo.
echo Individual dashboards (behind shell):
echo   Manager:   http://localhost:3001
echo   Marketing: http://localhost:3002
echo   Direction: http://localhost:3003
echo.
echo Demo Credentials (Password: password):
echo   manager@crmpharm.com
echo   marketing@crmpharm.com
echo   direction@crmpharm.com
echo.
echo Close any terminal window to stop that service.
echo.
timeout /t 3
