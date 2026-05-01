#!/bin/bash
# CRM Pharma — Run All Web Applications in Parallel

echo "==========================================="
echo "CRM Pharma — Starting All Dashboards"
echo "==========================================="
echo ""

# Check if npm exists
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm not found. Please install Node.js 18+"
    exit 1
fi

echo "Starting Manager Dashboard on port 3001..."
cd "$(dirname "$0")/manager_web" && npm run dev &

echo "Starting Marketing Dashboard on port 3002..."
cd "$(dirname "$0")/marketing_web" && npm run dev &

echo "Starting Direction Dashboard on port 3003..."
cd "$(dirname "$0")/direction_web" && npm run dev &

echo ""
echo "==========================================="
echo "All dashboards starting..."
echo "==========================================="
echo ""
echo "URLs:"
echo "  Manager:   http://localhost:3001"
echo "  Marketing: http://localhost:3002"
echo "  Direction: http://localhost:3003"
echo ""
echo "Credentials for all apps: password"
echo "  manager@crmpharm.com"
echo "  marketing@crmpharm.com"
echo "  direction@crmpharm.com"
echo ""
echo "Press Ctrl+C to stop all dashboards."
echo ""

# Wait for all background processes
wait
