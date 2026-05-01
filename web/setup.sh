#!/bin/bash
# CRM Pharma Web Setup Script (macOS/Linux)

echo "==========================================="
echo "CRM Pharma — Web Applications Setup"
echo "==========================================="
echo ""

# Check Node.js
echo "[1/5] Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found. Please install Node.js 18+"
    exit 1
fi
echo "OK - Node.js found: $(node -v)"

echo ""
echo "[2/5] Installing manager_web dependencies..."
cd manager_web || exit
npm install || exit
cd ..

echo ""
echo "[3/5] Installing marketing_web dependencies..."
cd marketing_web || exit
npm install || exit
cd ..

echo ""
echo "[4/5] Installing direction_web dependencies..."
cd direction_web || exit
npm install || exit
cd ..

echo ""
echo "[5/5] Creating .env files..."
[ ! -f "manager_web/.env" ] && cp manager_web/.env.example manager_web/.env && echo "Created manager_web/.env"
[ ! -f "marketing_web/.env" ] && cp marketing_web/.env.example marketing_web/.env && echo "Created marketing_web/.env"
[ ! -f "direction_web/.env" ] && cp direction_web/.env.example direction_web/.env && echo "Created direction_web/.env"

echo ""
echo "==========================================="
echo "Setup Complete!"
echo "==========================================="
echo ""
echo "Next Steps:"
echo ""
echo "Terminal 1 - Manager Dashboard (Port 3001):"
echo "  cd manager_web"
echo "  npm run dev"
echo ""
echo "Terminal 2 - Marketing Dashboard (Port 3002):"
echo "  cd marketing_web"
echo "  npm run dev"
echo ""
echo "Terminal 3 - Direction Dashboard (Port 3003):"
echo "  cd direction_web"
echo "  npm run dev"
echo ""
echo "Credentials:"
echo "  Manager:   manager@crmpharm.com / password"
echo "  Marketing: marketing@crmpharm.com / password"
echo "  Direction: direction@crmpharm.com / password"
echo ""
echo "Documentation: See README.md in each app folder"
echo ""
