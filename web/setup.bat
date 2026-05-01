@echo off
REM CRM Pharma Web Setup Script
REM Installs dependencies for all 3 web applications

echo ============================================
echo CRM Pharma — Web Applications Setup
echo ============================================
echo.

REM Check Node.js
echo [1/5] Checking Node.js...
node -v >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 18+
    exit /b 1
)
echo OK - Node.js found: 
node -v

echo.
echo [2/5] Installing manager_web dependencies...
cd manager_web
call npm install
if errorlevel 1 (
    echo ERROR: manager_web installation failed
    exit /b 1
)
cd ..

echo.
echo [3/5] Installing marketing_web dependencies...
cd marketing_web
call npm install
if errorlevel 1 (
    echo ERROR: marketing_web installation failed
    exit /b 1
)
cd ..

echo.
echo [4/5] Installing direction_web dependencies...
cd direction_web
call npm install
if errorlevel 1 (
    echo ERROR: direction_web installation failed
    exit /b 1
)
cd ..

echo.
echo [5/5] Creating .env files...
if not exist "manager_web\.env" (
    copy manager_web\.env.example manager_web\.env
    echo Created manager_web/.env
)
if not exist "marketing_web\.env" (
    copy marketing_web\.env.example marketing_web\.env
    echo Created marketing_web/.env
)
if not exist "direction_web\.env" (
    copy direction_web\.env.example direction_web\.env
    echo Created direction_web/.env
)

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Next Steps:
echo.
echo Terminal 1 - Manager Dashboard (Port 3001):
echo   cd manager_web
echo   npm run dev
echo.
echo Terminal 2 - Marketing Dashboard (Port 3002):
echo   cd marketing_web
echo   npm run dev
echo.
echo Terminal 3 - Direction Dashboard (Port 3003):
echo   cd direction_web
echo   npm run dev
echo.
echo Credentials:
echo   Manager:   manager@crmpharm.com / password
echo   Marketing: marketing@crmpharm.com / password
echo   Direction: direction@crmpharm.com / password
echo.
echo Documentation: See README.md in each app folder
echo.
pause
