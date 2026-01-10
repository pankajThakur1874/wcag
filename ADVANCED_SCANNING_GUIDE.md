# Advanced WCAG Scanning Solutions

This guide covers advanced solutions for:
1. ✅ Protected websites (Air India, sites with bot protection)
2. ✅ Interactive elements (tabs, modals, accordions, dropdowns)
3. ✅ Manual HTML scanning (offline scanning)

---

## 🛡️ Solution 1: Pa11y CI for Protected Websites

**When to use:** Sites with CAPTCHA, bot protection, or aggressive CDN filtering

### Setup

```bash
# Install Pa11y CI globally
npm install -g pa11y-ci

# Verify installation
pa11y-ci --version
```

### Configuration

The `.pa11yci.json` file is already configured with Air India URLs:

```json
{
  "defaults": {
    "timeout": 120000,
    "wait": 3000,
    "chromeLaunchConfig": {
      "args": ["--no-sandbox", "--disable-dev-shm-usage"]
    },
    "runners": ["axe"],
    "standard": "WCAG2AA"
  },
  "urls": [
    "https://www.airindia.com/",
    "https://www.airindia.com/in/en/about-us/our-story",
    // ... more URLs
  ]
}
```

### Run Scan

```bash
# Easy way: Use the provided script
./run_pa11y_scan.sh

# Manual way
pa11y-ci

# Custom URLs
pa11y-ci https://www.airindia.com/ https://www.airindia.com/contact
```

### Output

- `pa11y-results.json` - Machine-readable results
- `pa11y-report.html` - Human-readable report  
- `screenshots/` - Page screenshots

### Advantages

✅ Bypasses many bot protections
✅ Uses real Chrome browser
✅ Batch scanning multiple URLs
✅ Screenshot capture
✅ Multiple reporters (CLI, JSON, HTML)

### Limitations

❌ Still may be blocked by very aggressive protections
❌ Requires manual URL list (no crawling)
❌ Slower than built-in scanner

---

## 📄 Solution 2: Manual HTML Scanning (Offline)

**When to use:** Sites that are completely blocking automated access

### Workflow

#### Step 1: Save HTML Manually

1. Open the website in your browser (Chrome/Firefox)
2. Complete any CAPTCHA/authentication
3. Accept cookies, interact with page as needed
4. Right-click → "Save As" → "Webpage, Complete" or "Webpage, HTML Only"
5. Save to a folder (e.g., `~/Downloads/airindia_pages/`)

#### Step 2: Scan Saved HTML

```bash
# Scan single file
python scan_offline_html.py ~/Downloads/airindia.html

# Scan all HTML files in a directory
python scan_offline_html.py ~/Downloads/airindia_pages/
```

### Features

✅ Scans with all 15 scanners (including interactive!)
✅ Works on completely protected sites
✅ Batch scanning of multiple files
✅ Generates HTML + JSON reports
✅ No internet connection needed after saving

### Example Output

```
╔════════════════════════════════════════════════════════════╗
║  Offline HTML Scanner                                      ║
╚════════════════════════════════════════════════════════════╝

📄 File: airindia.html
📊 Size: 324.5 KB

🔍 Starting scan with all 15 scanners...

================================================================================
SCAN COMPLETE
================================================================================
Overall Score: 72%
Total Violations: 23

Violations by Impact:
  🔴 Critical: 0
  🟠 Serious:  5
  🟡 Moderate: 12
  🔵 Minor:    6

📊 Reports saved:
   - airindia_wcag_report.html
   - airindia_wcag_report.json

Open report: open airindia_wcag_report.html
```

### Tips

- Save complete page including CSS/JS when possible
- Save multiple states (before/after interactions)
- Name files descriptively (homepage.html, booking.html, etc.)
- Keep folder organized by section/feature

---

## 🎯 Solution 3: Interactive Element Scanner

**When to use:** Testing tabs, modals, accordions, dropdowns, expandable sections

### What It Does

The new **Interactive Scanner** automatically:
1. Discovers interactive elements on the page
2. Tests proper ARIA attributes
3. Simulates user interactions (clicks, keyboard)
4. Verifies state changes (aria-expanded, aria-selected)
5. Checks for accessibility issues

### Supported Elements

- **Tabs** - `[role="tab"]`, `[role="tablist"]`
- **Accordions** - `[aria-expanded]`, `.accordion`
- **Modals** - `[role="dialog"]`, `[data-modal]`
- **Dropdowns** - `[aria-haspopup]`, `.dropdown`

### Usage

```bash
# Run with interactive scanner included (now default)
python -m src.cli scan https://example.com -o report.json

# Run ONLY interactive scanner
python -m src.cli scan https://example.com -t interactive -o report.json

# Test interactive elements specifically
python test_interactive_scanner.py
```

### What It Checks

**Tabs:**
- ✅ Proper `role="tab"` attribute
- ✅ `aria-controls` pointing to panel
- ✅ `aria-selected` state management
- ✅ Keyboard accessibility (tabindex)
- ✅ Panel visibility on click

**Accordions:**
- ✅ `aria-expanded` attribute
- ✅ `aria-controls` attribute
- ✅ State toggles on interaction
- ✅ Keyboard navigation

**Modals:**
- ✅ `role="dialog"` or `role="alertdialog"`
- ✅ `aria-modal="true"`
- ✅ `aria-label` or `aria-labelledby`
- ✅ Close button present
- ✅ Escape key closes modal

**Dropdowns:**
- ✅ `aria-haspopup` attribute
- ✅ `aria-expanded` state
- ✅ Native `<select>` vs custom implementation

### Example Scan

```python
import asyncio
from src.core import ResultsAggregator

async def scan_with_interactions():
    # Include interactive scanner
    aggregator = ResultsAggregator(tools=['axe', 'interactive'])
    result = await aggregator.scan('https://yoursite.com')
    
    # Check interactive violations
    interactive_issues = [v for v in result.violations if 'interactive' in v.detected_by]
    
    print(f"Found {len(interactive_issues)} interactive element issues")
    for issue in interactive_issues:
        print(f"- {issue.description}")

asyncio.run(scan_with_interactions())
```

---

## 🔄 Complete Workflow for Air India

Here's how to comprehensively scan Air India:

### Step 1: Identify Pages to Scan

```bash
# List of important pages
pages=(
  "/"
  "/about-us"
  "/web-check-in"
  "/book-flight"
  "/manage-booking"
  "/baggage"
  "/contact-us"
)
```

### Step 2: Option A - Pa11y CI (If it works)

```bash
# Edit .pa11yci.json with your URLs
# Run scan
./run_pa11y_scan.sh
```

### Step 3: Option B - Manual HTML Capture (Most reliable)

```bash
# 1. Create folder
mkdir -p airindia_scans

# 2. For each important page:
#    - Open in browser
#    - Complete CAPTCHA
#    - Accept cookies
#    - Save as HTML

# 3. Scan all saved pages
python scan_offline_html.py airindia_scans/
```

### Step 4: Interactive Elements (After saving HTML)

```bash
# Scan saved pages with interactive scanner
python -m src.cli scan file:///path/to/airindia_homepage.html \
  -t interactive -o airindia_interactive_report.json
```

### Step 5: Aggregate Results

```python
# Create comprehensive report from all scans
import json
import glob

all_violations = []
all_scores = []

# Load all JSON reports
for report_file in glob.glob("*_wcag_report.json"):
    with open(report_file) as f:
        data = json.load(f)
        all_violations.extend(data.get('violations', []))
        all_scores.append(data.get('scores', {}).get('overall', 0))

# Calculate overall
avg_score = sum(all_scores) / len(all_scores)
print(f"Average Score: {avg_score}%")
print(f"Total Issues: {len(all_violations)}")
```

---

## 📊 Comparison of Solutions

| Feature | Built-in Scanner | Pa11y CI | Manual HTML | Interactive Scanner |
|---------|-----------------|----------|-------------|-------------------|
| **Auto crawling** | ✅ | ❌ | ❌ | N/A |
| **Protected sites** | ❌ | Partial | ✅ | Via saved HTML |
| **Interactive elements** | Limited | Limited | Via scanner | ✅ |
| **Speed** | Fast | Medium | Fast | Medium |
| **Setup complexity** | Low | Medium | Low | Low |
| **Offline scanning** | ❌ | ❌ | ✅ | ✅ |
| **Best for** | Public sites | Semi-protected | Fully protected | UI components |

---

## 🎯 Recommendations by Scenario

### Scenario 1: Regular Public Website
```bash
python test_site_scan.py
# Uses built-in crawler + all 15 scanners
```

### Scenario 2: Protected Website (CAPTCHA)
```bash
# Option A: Try Pa11y CI first
./run_pa11y_scan.sh

# Option B: Manual HTML if Pa11y fails
# 1. Save pages manually
# 2. python scan_offline_html.py saved_pages/
```

### Scenario 3: Complex Interactive UI
```bash
# Scan with interactive scanner emphasis
python -m src.cli scan https://site.com \
  -t axe -t interactive -t aria -o report.json
```

### Scenario 4: Complete Audit (Air India)
```bash
# 1. Manual HTML capture for all pages
# 2. Offline scan with all scanners
python scan_offline_html.py airindia_pages/

# 3. Specific interactive testing
for file in airindia_pages/*.html; do
  python -m src.cli scan "file://$file" -t interactive -o "$(basename $file .html)_interactive.json"
done
```

---

## 🚀 Quick Reference

| Task | Command |
|------|---------|
| Scan protected site (Pa11y) | `./run_pa11y_scan.sh` |
| Scan saved HTML file | `python scan_offline_html.py file.html` |
| Scan saved HTML folder | `python scan_offline_html.py folder/` |
| Test interactive elements | `python test_interactive_scanner.py` |
| Scan with interactive scanner | `python -m src.cli scan URL -t interactive` |
| List all scanners | `python -m src.cli tools` |

---

## 💡 Pro Tips

1. **For Protected Sites:**
   - Try Pa11y CI first (faster)
   - Fall back to manual HTML if needed
   - Use browser extensions for one-off checks

2. **For Interactive Elements:**
   - Use interactive scanner on saved HTML
   - Test different states (expanded/collapsed)
   - Save page in each state if needed

3. **Batch Processing:**
   - Use Pa11y CI for list of URLs
   - Use offline scanner for saved HTML batch
   - Aggregate results with custom scripts

4. **Best Results:**
   - Combine multiple approaches
   - Test with different scanners
   - Verify critical user flows manually

---

## 📞 Getting Help

- Built-in scanner issues: Check `COMPLETE_SCANNING_GUIDE.md`
- Pa11y CI docs: https://github.com/pa11y/pa11y-ci
- Interactive scanner: See `src/scanners/interactive_scanner.py`
- Report bugs: Create issue in project repo

---

## 🎉 You Now Have 15 Scanners!

1. axe (axe-core)
2. pa11y (external)
3. lighthouse (external)
4. html_validator
5. contrast
6. keyboard
7. aria
8. seo
9. forms
10. link_text
11. image_alt
12. media
13. touch_target
14. readability
15. **interactive** ← NEW!

All solutions are ready to use! 🚀
