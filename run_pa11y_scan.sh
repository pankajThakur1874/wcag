#!/bin/bash

# Pa11y CI Scanner for Protected Websites
# This bypasses some bot protection by using a real browser

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Pa11y CI Scanner for Protected Websites                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Pa11y CI is installed
if ! command -v pa11y-ci &> /dev/null; then
    echo "❌ Pa11y CI not found. Installing..."
    npm install -g pa11y-ci
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install Pa11y CI"
        echo "Please run manually: npm install -g pa11y-ci"
        exit 1
    fi
    echo "✅ Pa11y CI installed successfully"
fi

# Create screenshots directory
mkdir -p screenshots

echo ""
echo "📊 Starting scan..."
echo "URLs configured in .pa11yci.json"
echo ""

# Run Pa11y CI
pa11y-ci

# Check result
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Scan completed successfully!"
    echo ""
    echo "📁 Results saved:"
    echo "   - pa11y-results.json (JSON data)"
    echo "   - pa11y-report.html (Visual report)"
    echo "   - screenshots/ (Page screenshots)"
    echo ""
    echo "Open report: open pa11y-report.html"
else
    echo ""
    echo "⚠️  Scan completed with issues"
    echo "Check pa11y-results.json for details"
fi
