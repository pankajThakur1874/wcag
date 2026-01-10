# Quick Start: Comprehensive Website Scanning

## 🚀 3 Ways to Scan Entire Websites

### Method 1: Site Scanner (Built-in - Best for Simple Sites)

```python
# Run the test script
python test_site_scan.py

# Or customize:
python -c "
import asyncio
from src.core import SiteScanner

async def scan():
    scanner = SiteScanner(max_pages=50, max_depth=3)
    result = await scanner.scan_site('https://yoursite.com')
    print(f'Score: {result.overall_score}%')
    print(f'Pages: {result.pages_scanned}')
    
asyncio.run(scan())
"
```

### Method 2: API (Built-in - Best for Production)

```bash
# 1. Start server
python main.py &

# 2. Scan entire site
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://yoursite.com/",
    "site_wide": true,
    "max_pages": 100,
    "max_depth": 3
  }'

# Returns: {"scan_id": "abc-123"}

# 3. Get results
curl "http://localhost:8000/api/v1/scan/abc-123" | jq

# 4. Download report
curl "http://localhost:8000/api/v1/scan/abc-123/download?format=html" > report.html
```

### Method 3: External Tools (Best for Complex Sites)

**Pa11y CI** (Recommended for protected sites like Air India)
```bash
npm install -g pa11y-ci

# Create .pa11yci.json
echo '{
  "urls": [
    "https://www.airindia.com/",
    "https://www.airindia.com/about",
    "https://www.airindia.com/contact"
  ],
  "defaults": {
    "timeout": 60000,
    "wait": 2000,
    "runners": ["axe"]
  }
}' > .pa11yci.json

# Run scan
pa11y-ci
```

**Lighthouse CI** (Google's tool)
```bash
npm install -g @lhci/cli

# Scan multiple pages
lhci autorun \
  --collect.url=https://www.airindia.com/ \
  --collect.url=https://www.airindia.com/about \
  --collect.url=https://www.airindia.com/contact
```

**axe-core CLI** (Industry standard)
```bash
npm install -g @axe-core/cli

# Scan with sitemap
axe https://yoursite.com --sitemap https://yoursite.com/sitemap.xml

# Or scan multiple URLs
axe https://site.com/ https://site.com/page1 https://site.com/page2
```

---

## 🛡️ For Protected Websites (Air India)

### Option A: Manual HTML Capture
```bash
# 1. Open browser, navigate to Air India
# 2. Complete CAPTCHA, accept cookies
# 3. Save page: Right-click → Save As → "Complete"
# 4. Scan local file:
python -m src.cli scan file:///path/to/airindia.html -o report.json
```

### Option B: WAVE Standalone (Desktop App)
- Download: https://wave.webaim.org/standalone
- Runs like regular browser
- No bot detection
- Batch scan multiple pages
- Cost: ~$50/year

### Option C: Browser Extensions
- **axe DevTools**: https://www.deque.com/axe/browser-extensions/
- **WAVE**: https://wave.webaim.org/extension/
- **Lighthouse**: Built into Chrome DevTools (F12 → Lighthouse tab)

---

## 🎯 Recommended Workflow

### For Public Websites:
```bash
# Use built-in scanner
python test_site_scan.py
```

### For Protected Websites:
```bash
# Use Pa11y CI with manual URL list
npm install -g pa11y-ci
# Edit .pa11yci.json with URLs
pa11y-ci
```

### For SPAs (React/Vue/Angular):
```bash
# Method 1: Extract routes from sitemap.xml
# Method 2: Manual URL list
# Method 3: Use Lighthouse CI with --collect.url for each route
```

### For Enterprise/Production:
- Consider **axe Monitor** (paid, best-in-class)
- Or **Siteimprove** (enterprise platform)
- Handles: Authentication, bot protection, SPAs, dynamic content

---

## 📊 What You Get

### Built-in Scanner Reports:
- ✅ Per-page scores and violations
- ✅ Aggregated statistics
- ✅ Worst/best pages
- ✅ Violations grouped by impact
- ✅ WCAG 2.2 compliance mapping
- ✅ HTML + JSON reports

### Example Output:
```
Pages scanned: 25
Overall score: 78%
Unique violations: 45
Critical: 2
Serious: 12
Moderate: 18
Minor: 13
```

---

## 💡 Pro Tips

1. **Start small**: Test with max_pages=10 first
2. **Increase depth gradually**: depth=2 usually sufficient
3. **Use concurrent_scans**: Set to 3-5 for speed
4. **Check robots.txt**: Some sites block crawlers
5. **Respect rate limits**: Don't overwhelm servers
6. **Save results**: Always export to JSON for records
7. **Combine tools**: Use multiple scanners for better coverage

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Test site scanner | `python test_site_scan.py` |
| Start API server | `python main.py` |
| Single page scan | `python -m src.cli scan URL -o report.json` |
| List scanners | `python -m src.cli tools` |
| API docs | Visit http://localhost:8000/docs |
| Read full guide | `cat COMPLETE_SCANNING_GUIDE.md` |

---

## 🆘 Troubleshooting

**Site timing out (like Air India)?**
→ Use Pa11y CI or browser extensions instead

**Only 1 page found?**
→ Site uses JavaScript navigation. Manually list URLs.

**Bot protection detected?**
→ Use WAVE Standalone or manual HTML capture

**Need to scan 1000+ pages?**
→ Consider commercial tools (axe Monitor, Siteimprove)

**SPA not crawling properly?**
→ Extract routes from sitemap.xml or app router

---

## 🎉 Ready to Go!

You now have **5 comprehensive solutions**:

1. ✅ **Built-in Site Scanner** (working)
2. ✅ **API-based scanning** (working)
3. ✅ **Pa11y CI** (for protected sites)
4. ✅ **Browser extensions** (manual testing)
5. ✅ **Commercial tools** (enterprise needs)

Start with: `python test_site_scan.py`

For full details: `cat COMPLETE_SCANNING_GUIDE.md`
