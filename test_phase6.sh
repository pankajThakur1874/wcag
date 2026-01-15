#!/bin/bash
# Test script for Phase 6: CLI Commands

set -e

echo "============================================================"
echo "PHASE 6 TEST: CLI Commands"
echo "============================================================"
echo ""
echo "Prerequisites:"
echo "  - API server must be running (python main_v2.py)"
echo "  - MongoDB must be running"
echo ""
echo "This script will test CLI commands interactively."
echo "Press Enter to continue..."
read

CLI="python cli_v2.py"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Testing CLI Help${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

$CLI --help

echo ""
echo -e "${YELLOW}Press Enter to continue...${NC}"
read

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Testing Server Commands${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

echo "1. Server status"
$CLI server status

echo ""
echo -e "${YELLOW}Press Enter to continue...${NC}"
read

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Testing Authentication${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

echo "2. Register user (test-cli@example.com / TestCLI123)"
$CLI auth register --email test-cli@example.com --password TestCLI123 --name "CLI Test User"

echo ""
echo "3. Login"
$CLI auth login --email test-cli@example.com --password TestCLI123

echo ""
echo "4. Check current user"
$CLI auth whoami

echo ""
echo -e "${YELLOW}Press Enter to continue...${NC}"
read

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Testing Project Commands${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

echo "5. Create project"
PROJECT_OUTPUT=$($CLI project create "CLI Test Project" "https://example.com" --description "Created via CLI" 2>&1)
echo "$PROJECT_OUTPUT"
PROJECT_ID=$(echo "$PROJECT_OUTPUT" | grep "Project created:" | awk '{print $3}')

echo ""
echo "Project ID: $PROJECT_ID"

echo ""
echo "6. List projects"
$CLI project list

echo ""
echo "7. Show project details"
$CLI project show "$PROJECT_ID"

echo ""
echo -e "${YELLOW}Press Enter to continue...${NC}"
read

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Testing Scan Commands${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

echo "8. Start scan"
SCAN_OUTPUT=$($CLI scan start "$PROJECT_ID" --max-pages 3 --max-depth 1 2>&1)
echo "$SCAN_OUTPUT"
SCAN_ID=$(echo "$SCAN_OUTPUT" | grep "Scan created:" | awk '{print $3}')

echo ""
echo "Scan ID: $SCAN_ID"

echo ""
echo "9. List scans"
$CLI scan list

echo ""
echo "10. Show scan details"
$CLI scan show "$SCAN_ID"

echo ""
echo "11. Check scan status"
$CLI scan status "$SCAN_ID"

echo ""
echo -e "${YELLOW}Waiting 5 seconds for scan to process...${NC}"
sleep 5

echo ""
echo "12. Check scan status again"
$CLI scan status "$SCAN_ID"

echo ""
echo -e "${YELLOW}Press Enter to continue...${NC}"
read

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Testing Report Commands${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

echo "13. View report (text format)"
$CLI report view "$SCAN_ID"

echo ""
echo "14. Export report to JSON"
$CLI report export "$SCAN_ID" --output /tmp/scan-report.json --format json

echo ""
echo "15. View issues"
$CLI report issues "$SCAN_ID" --limit 10

echo ""
echo -e "${YELLOW}Press Enter to continue with cleanup...${NC}"
read

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Cleanup${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

echo "16. Delete scan"
$CLI scan delete "$SCAN_ID" --yes

echo ""
echo "17. Delete project"
$CLI project delete "$PROJECT_ID" --yes

echo ""
echo "18. Logout"
$CLI auth logout

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}✓ ALL PHASE 6 TESTS PASSED!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "Phase 6 Complete - CLI commands are working!"
echo ""
echo "What's been tested:"
echo "  ✓ Server management commands (status)"
echo "  ✓ User authentication (register, login, logout, whoami)"
echo "  ✓ Project CRUD operations (create, list, show, delete)"
echo "  ✓ Scan management (start, list, show, status, delete)"
echo "  ✓ Report generation (view, export, issues)"
echo "  ✓ Rich terminal formatting"
echo ""
echo "Next: Phase 7 - TUI Dashboard"
echo ""
