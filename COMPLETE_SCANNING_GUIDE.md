# Complete Website WCAG Scanning Guide

## 🎯 Overview

This guide covers **all methods** to scan entire websites for WCAG compliance, including:
1. Built-in site-wide scanner (API & programmatic)
2. Alternative solutions for protected websites
3. Handling dynamic interactions & SPAs
4. Commercial and open-source alternatives

---

## ✅ Solution 1: Built-In Site Scanner (BEST for Most Cases)

Your project has a **powerful site-wide scanner** already built-in!

### Features:
- ✅ Crawls entire website automatically
- ✅ Scans every discovered page with all 14 scanners
- ✅ Handles concurrent scanning (multiple pages at once)
- ✅ Deduplicates violations across pages
- ✅ Respects robots.txt
- ✅ Configurable depth and page limits
- ✅ Progress tracking
- ✅ Aggregated reports with per-page breakdowns

### Method A: Using the FastAPI (Recommended for Production)

```bash
# 1. Start the API server
python main.py

# Server runs on http://localhost:8000
```

```bash
# 2. Start a site-wide scan via API
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.britishairways.com/",
    "site_wide": true,
    "max_pages": 50,
    "max_depth": 3,
    "tools": null
  }'

# Response: {"scan_id": "abc-123", "status": "pending"}
```

```bash
# 3. Check scan progress
curl "http://localhost:8000/api/v1/scan/{scan_id}"

# 4. Download complete report when done
curl "http://localhost:8000/api/v1/scan/{scan_id}/download?format=html" > report.html
curl "http://localhost:8000/api/v1/scan/{scan_id}/download?format=json" > report.json
```

### Method B: Using Python Directly

```python
import asyncio
from src.core import SiteScanner

async def main():
    scanner = SiteScanner(
        max_pages=50,         # Scan up to 50 pages
        max_depth=3,          # Crawl 3 levels deep
        tools=None,           # Use all 14 scanners
        concurrent_scans=3    # Scan 3 pages simultaneously
    )
    
    # Optional: Monitor progress
    def on_progress(phase, current, total, message):
        print(f"[{phase}] {current}/{total}: {message}")
    
    scanner.set_progress_callback(on_progress)
    
    # Run scan
    result = await scanner.scan_site("https://example.com")
    
    # Access results
    print(f"Scanned {result.pages_scanned} pages")
    print(f"Overall score: {result.overall_score}%")
    print(f"Unique violations: {len(result.unique_violations)}")
    
    # Save report
    with open("report.json", "w") as f:
        json.dump(result.to_dict(), f, indent=2, default=str)

asyncio.run(main())
```

### What It Does:

1. **Crawling Phase**: Discovers all pages
   - Starts from homepage
   - Extracts all `<a href>` links
   - Follows links up to max_depth
   - Filters out images, PDFs, external domains
   - Skips /admin, /login, /cart paths

2. **Scanning Phase**: Tests each page
   - Runs all 14 scanners on each page
   - Scans multiple pages concurrently
   - Handles errors gracefully
   - Tracks success/failure per page

3. **Report Generation**: Aggregates results
   - Deduplicates violations across pages
   - Calculates overall score
   - Identifies worst/best pages
   - Groups violations by impact & WCAG level

### Limitations:

❌ **Does NOT handle**:
- Interactive clicks (dropdowns, modals, tabs)
- Single Page Applications (SPA) with JS routing
- Content behind login/authentication
- Dynamic content loaded on scroll
- Protected websites (like Air India)

---

## 🔧 Solution 2: Extended Scanner for Interactive Elements

For handling clicks, interactions, and dynamic content, you need to **enhance the scanner**:

### Approach A: Manual Click Paths

```python
from src.core import ResultsAggregator

# Define interaction sequences
interactions = [
    {
        "url": "https://example.com",
        "actions": [
            {"type": "click", "selector": "#menu-button"},
            {"type": "wait", "ms": 500},
            {"type": "click", "selector": "#submenu-item"}
        ]
    }
]

# Scan each interaction state
for interaction in interactions:
    result = await aggregator.scan(interaction["url"])
    # Perform actions on page...
```

### Approach B: Auto-Discovery of Interactive Elements

Enhancement needed in `/src/core/aggregator.py`:

```python
async def scan_with_interactions(self, url: str):
    # 1. Scan initial page
    # 2. Find all interactive elements (buttons, tabs, accordions)
    # 3. For each element:
    #    - Click it
    #    - Wait for changes
    #    - Scan new state
    #    - Restore original state
```

---

## 💡 Solution 3: SPA (Single Page Application) Scanning

For React, Vue, Angular apps with client-side routing:

### Tools to Use:

1. **Sitemap.xml**: If the SPA has a sitemap, crawl all URLs listed

```python
import xml.etree.ElementTree as ET
import httpx

async def scan_from_sitemap(sitemap_url):
    response = await httpx.get(sitemap_url)
    root = ET.fromstring(response.content)
    
    urls = [elem.text for elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    
    for url in urls:
        await aggregator.scan(url)
```

2. **JavaScript Route Discovery**: Parse the SPA bundle to find routes

3. **Manual URL List**: Provide all app routes manually

---

## 🛡️ Solution 4: Protected Websites (like Air India)

For sites with bot protection, CAPTCHA, or authentication:

### Option A: Authenticated Scanning

```python
async with browser_manager.get_page(url) as page:
    # 1. Navigate to login
    await page.goto("https://example.com/login")
    
    # 2. Fill credentials
    await page.fill("#username", "your_username")
    await page.fill("#password", "your_password")
    await page.click("#login-button")
    
    # 3. Wait for auth
    await page.wait_for_selector("#dashboard")
    
    # 4. Now scan authenticated pages
    # ...
```

### Option B: Manual HTML Capture

```bash
# 1. Open browser manually and navigate to site
# 2. Accept cookies, complete CAPTCHA, etc.
# 3. Save page HTML (Right-click → Save As → "Webpage, Complete")
# 4. Scan the saved HTML:

python -m src.cli scan file:///path/to/saved/page.html -o report.json
```

### Option C: Browser Extension Method

Use browser-based tools that don't get blocked:
- axe DevTools Chrome Extension
- WAVE Chrome Extension
- Lighthouse in Chrome DevTools

---

## 🌐 Solution 5: Commercial & Open Source Alternatives

### Commercial Solutions (Most Comprehensive)

1. **Deque axe Monitor** ($$$)
   - Best-in-class automated scanning
   - Handles SPAs, dynamic content
   - Authenticated scanning
   - 100+ page scans per month
   - CI/CD integration
   - https://www.deque.com/axe/monitor/

2. **Siteimprove** ($$$$)
   - Enterprise-grade platform
   - Full site crawling
   - Trend analysis over time
   - Manual audit support
   - https://siteimprove.com/

3. **Level Access** ($$$)
   - Combines automated + manual testing
   - WCAG 2.2, Section 508, ADA compliance
   - https://www.levelaccess.com/

4. **WAVE Standalone** ($)
   - Desktop application
   - No browser detection
   - Batch scanning
   - https://wave.webaim.org/standalone

### Open Source Solutions (Free)

1. **Pa11y CI** ⭐ Recommended
   ```bash
   npm install -g pa11y-ci
   
   # Create .pa11yci.json config
   {
     "urls": [
       "https://example.com",
       "https://example.com/about",
       "https://example.com/contact"
     ],
     "defaults": {
       "runners": ["axe", "htmlcs"]
     }
   }
   
   # Run batch scan
   pa11y-ci
   ```

2. **Lighthouse CI**
   ```bash
   npm install -g @lhci/cli
   
   # Scan multiple URLs
   lhci autorun --collect.url=https://example.com \
                --collect.url=https://example.com/about
   ```

3. **axe-core CLI**
   ```bash
   npm install -g @axe-core/cli
   
   # Scan with sitemap
   axe https://example.com --sitemap https://example.com/sitemap.xml
   ```

4. **AccessLint** (GitHub Integration)
   - Automated PR comments for accessibility issues
   - https://github.com/accesslint/accesslint.js

---

## 📊 Hybrid Approach: Best of All Worlds

**Recommended Production Setup**:

1. **Automated Crawling**: Use your built-in scanner for public pages
   ```python
   scanner = SiteScanner(max_pages=100, max_depth=3)
   result = await scanner.scan_site("https://example.com")
   ```

2. **Critical User Flows**: Manually define important interaction paths
   ```python
   critical_flows = [
       {"url": "/checkout", "actions": [...]},
       {"url": "/search", "actions": [...]}
   ]
   ```

3. **Manual Audits**: Use browser extensions for complex interactions

4. **CI/CD Integration**: Run on every deployment
   ```bash
   # In your CI pipeline
   python test_site_scan.py
   if [ $? -ne 0 ]; then
     echo "Accessibility issues found!"
     exit 1
   fi
   ```

5. **Periodic Deep Scans**: Use commercial tools quarterly for comprehensive audits

---

## 🚀 Quick Start Examples

### Example 1: Scan Your Entire Website (Up to 50 pages)

```bash
# Start API server
python main.py &

# Trigger scan
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://yourwebsite.com/", "site_wide": true, "max_pages": 50}'
```

### Example 2: Scan Specific Pages

```python
# test_specific_pages.py
import asyncio
from src.core import ResultsAggregator

async def scan_important_pages():
    pages = [
        "https://example.com/",
        "https://example.com/about",
        "https://example.com/products",
        "https://example.com/contact"
    ]
    
    aggregator = ResultsAggregator()
    
    for url in pages:
        result = await aggregator.scan(url)
        print(f"{url}: Score {result.scores.overall}%")

asyncio.run(scan_important_pages())
```

### Example 3: Run the Demo

```bash
# Run the included test script
python test_site_scan.py

# This will:
# - Crawl British Airways website
# - Scan discovered pages
# - Generate site_wide_report.json
```

---

## 📋 Feature Comparison

| Feature | Your Scanner | Pa11y CI | Lighthouse CI | Axe Monitor | Siteimprove |
|---------|-------------|----------|---------------|-------------|-------------|
| Auto crawl | ✅ | ❌ | ❌ | ✅ | ✅ |
| Multi-scanner | ✅ (14) | ✅ (3) | ✅ (1) | ✅ (1) | ✅ (Multiple) |
| Interactive clicks | ❌ | ❌ | ❌ | ✅ | ✅ |
| SPA support | Partial | ❌ | Partial | ✅ | ✅ |
| Authentication | Manual | Manual | Manual | ✅ | ✅ |
| Bot protection bypass | ❌ | ❌ | ❌ | ✅ | ✅ |
| Cost | Free | Free | Free | Paid | Paid |
| Custom rules | ✅ | ✅ | ❌ | ✅ | ✅ |

---

## 🎯 Recommendations

**For Your Use Case (Air India + Comprehensive Scanning):**

1. **Immediate**: Use the built-in site scanner for accessible websites
   ```bash
   python test_site_scan.py
   ```

2. **Air India Specific**: 
   - Try manual HTML capture method
   - OR use WAVE Standalone desktop app
   - OR request audit access from Air India IT team

3. **Long-term**: 
   - Enhance scanner with interaction support
   - Integrate Pa11y CI for CI/CD
   - Consider axe Monitor for protected sites

---

## 📞 Next Steps

1. Try the site scanner now:
   ```bash
   python test_site_scan.py
   ```

2. Start API server and test via web interface:
   ```bash
   python main.py
   # Visit http://localhost:8000/docs
   ```

3. For Air India, try:
   - Sub-pages (less protected)
   - Manual HTML capture
   - Browser extensions

