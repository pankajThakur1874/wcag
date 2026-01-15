# Phase 8 Test Guide: Report Generation

## Prerequisites

1. **API Server Running**:
   ```bash
   python main_v2.py
   ```

2. **MongoDB Running**:
   ```bash
   docker run -d -p 27017:27017 --name mongodb mongo:7
   ```

3. **User Authenticated**:
   ```bash
   python cli_v2.py auth login --email user@example.com --password Pass123
   ```

4. **Completed Scan with Data**:
   ```bash
   # Create a project
   python cli_v2.py project create "Test Site" "https://example.com"

   # Note the project ID from the output, then start a scan
   python cli_v2.py scan start <PROJECT_ID> --max-pages 5 --wait

   # Note the scan ID from the output for testing reports
   ```

## Phase 8 Features to Test

### 1. JSON Report (Already Implemented)

Test JSON report generation:

```bash
# View JSON report in terminal
python cli_v2.py report view <SCAN_ID> --format json

# Export JSON report to file
python cli_v2.py report export <SCAN_ID> -o reports/scan_report.json -f json
```

**Verify**:
- JSON is well-formatted and readable
- Contains all sections: scan, project, summary, scores, pages, issues, metadata
- Issue data includes: rule_id, description, impact, WCAG criteria, etc.
- Scores show overall and by principle

### 2. HTML Report (New in Phase 8)

Test HTML report generation:

```bash
# Export HTML report to file
python cli_v2.py report export <SCAN_ID> -o reports/scan_report.html -f html

# Open in browser (macOS)
open reports/scan_report.html

# Open in browser (Linux)
xdg-open reports/scan_report.html

# Or use the file path shown in the CLI output
```

**Verify HTML Report Features**:

#### Executive Summary
- [ ] Overall compliance score displayed prominently
- [ ] Score circle with color coding (green ≥90, blue ≥70, yellow ≥50, red <50)
- [ ] WCAG Principles scores with progress bars
- [ ] Summary statistics cards (pages, issues, critical, serious, moderate, minor)
- [ ] WCAG level compliance (A, AA, AAA issue counts)

#### Issues by Impact
- [ ] Filter buttons work (All, Critical, Serious, Moderate, Minor)
- [ ] Issues grouped by impact level with color-coded headings
- [ ] Each issue card shows:
  - Impact badge with correct color
  - WCAG criteria badges
  - Description and rule ID
  - WCAG principle and detected by scanners
  - Help text and help URL link
  - Fix suggestions (if available)
  - Expandable instances section
- [ ] Clicking filter buttons shows/hides appropriate issue groups

#### Issues by WCAG Criteria
- [ ] Issues organized by WCAG criterion (e.g., 1.1.1, 1.4.3)
- [ ] Each criterion shows issue count
- [ ] Issues listed with impact badges
- [ ] Instance counts displayed

#### Page-by-Page Analysis
- [ ] Table with all scanned pages
- [ ] Columns: URL, Title, Issues, Score, Load Time, Status
- [ ] URLs are clickable links
- [ ] Issue counts displayed with badges
- [ ] Scores color-coded (same as overall score)
- [ ] Status codes shown (200, 404, 500, etc.)
- [ ] Table rows highlight on hover

#### WCAG Compliance Checklist
- [ ] Organized by Level A, AA, AAA
- [ ] Each criterion shows passed/failed status
- [ ] Checkmarks (✓) for passed criteria
- [ ] Cross marks (✗) for failed criteria
- [ ] Issue counts shown for failed criteria
- [ ] Color coding (green for passed, red for failed)

#### Visual Design
- [ ] Professional, clean layout
- [ ] Responsive design (works on mobile)
- [ ] Print-friendly styling
- [ ] Gradient header background
- [ ] Proper spacing and typography
- [ ] Accessible color contrasts (dogfooding!)
- [ ] Icons and badges clearly visible

#### Functionality
- [ ] Filter buttons work correctly
- [ ] Details/summary elements expand/collapse
- [ ] Links open in new tabs
- [ ] Ctrl+P / Cmd+P triggers print preview
- [ ] Page scrolls smoothly
- [ ] No JavaScript errors in console

### 3. CSV Report (New in Phase 8)

Test CSV export:

```bash
# Export CSV report to file
python cli_v2.py report export <SCAN_ID> -o reports/scan_report.csv -f csv

# View CSV (macOS)
open reports/scan_report.csv

# View CSV in terminal
cat reports/scan_report.csv | head -20
```

**Verify CSV Format**:
- [ ] Header row with correct column names
- [ ] Columns: Issue ID, Page URL, Page Title, Rule ID, Description, Impact, WCAG Level, WCAG Criteria, Principle, Help Text, Help URL, Detected By, Instances Count, Status, Manual Review Required, Fix Suggestion
- [ ] Data properly escaped (no broken CSV due to commas/quotes)
- [ ] Opens correctly in Excel/Google Sheets
- [ ] Can be filtered and sorted in spreadsheet software
- [ ] UTF-8 encoding preserves special characters

### 4. API Endpoints

Test API endpoints directly:

#### JSON Report Endpoint
```bash
# Get your auth token
TOKEN=$(python cli_v2.py auth whoami | grep "Token" | awk '{print $2}')

# Test JSON endpoint
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/scans/<SCAN_ID>/reports/json | jq '.'
```

**Verify**:
- Returns 200 status code
- Returns valid JSON
- Contains all expected fields

#### HTML Report Endpoint
```bash
# Test HTML endpoint
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/scans/<SCAN_ID>/reports/html > test.html

# Open in browser
open test.html
```

**Verify**:
- Returns 200 status code
- Returns valid HTML
- HTML renders correctly in browser

#### CSV Report Endpoint
```bash
# Test CSV endpoint
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/scans/<SCAN_ID>/reports/csv > test.csv

# View CSV
cat test.csv | head -10
```

**Verify**:
- Returns 200 status code
- Returns valid CSV
- CSV header is correct

### 5. Error Handling

Test error scenarios:

#### Non-existent Scan
```bash
# Try to export report for non-existent scan
python cli_v2.py report export fake-scan-id -o report.html -f html
```

**Expected**: Error message "Scan not found"

#### Not Authenticated
```bash
# Logout and try to export
python cli_v2.py auth logout
python cli_v2.py report export <SCAN_ID> -o report.html -f html
```

**Expected**: Error message "Not authenticated"

#### Access Denied (Different User's Scan)
If you have multiple users, try accessing another user's scan:

**Expected**: Error message "Access denied to this scan"

### 6. CLI Report Commands

Test all CLI report commands:

#### View Report
```bash
# View text report in terminal
python cli_v2.py report view <SCAN_ID>

# View JSON report
python cli_v2.py report view <SCAN_ID> --format json
```

#### Export Report
```bash
# Export all formats
python cli_v2.py report export <SCAN_ID> -o reports/report.json -f json
python cli_v2.py report export <SCAN_ID> -o reports/report.html -f html
python cli_v2.py report export <SCAN_ID> -o reports/report.csv -f csv
```

#### List Issues
```bash
# List all issues
python cli_v2.py report issues <SCAN_ID>

# Filter by impact
python cli_v2.py report issues <SCAN_ID> --impact critical

# Filter by WCAG level
python cli_v2.py report issues <SCAN_ID> --wcag-level AA

# Limit results
python cli_v2.py report issues <SCAN_ID> --limit 10
```

## Performance Testing

### Large Scans

Test with larger scans:

```bash
# Create a scan with more pages
python cli_v2.py scan start <PROJECT_ID> --max-pages 50 --wait
```

**Verify**:
- HTML report generates in reasonable time (<10 seconds)
- CSV export completes successfully
- Large HTML files open without issues
- Browser doesn't freeze loading large reports

## Browser Compatibility

Test HTML reports in multiple browsers:

- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge
- [ ] Mobile browsers (responsive design)

## Accessibility Testing

Since this is an accessibility tool, the reports should be accessible:

- [ ] Run HTML report through its own scanner (dogfooding!)
- [ ] Check keyboard navigation works
- [ ] Verify screen reader compatibility
- [ ] Check color contrast ratios
- [ ] Ensure semantic HTML structure

## Test Results Checklist

- [ ] JSON reports export correctly
- [ ] HTML reports generate with all sections
- [ ] HTML reports display correctly in browsers
- [ ] CSS styling is applied properly
- [ ] CSV exports contain all issue data
- [ ] CSV opens correctly in spreadsheet software
- [ ] API endpoints return correct responses
- [ ] CLI commands work as expected
- [ ] Error handling works for invalid inputs
- [ ] Reports work for scans with no issues
- [ ] Reports work for scans with many issues
- [ ] Filters work in HTML reports
- [ ] Print styling works
- [ ] Responsive design works on mobile
- [ ] Reports are accessible

## Common Issues

### Issue: "Template not found"
**Solution**: Ensure `scanner_v2/report_templates/` directory exists with `html_report.jinja2` and `styles.css`

### Issue: CSS not loading in HTML report
**Solution**: CSS is inlined in the HTML. Check that `styles.css` exists and is being read correctly.

### Issue: CSV has broken formatting
**Solution**: Ensure special characters are properly escaped. Check for commas and quotes in issue descriptions.

### Issue: HTML report is blank
**Solution**: Check browser console for JavaScript errors. Verify scan has data (pages and issues).

### Issue: Export fails with permission error
**Solution**: Ensure output directory exists and you have write permissions.

## Success Criteria

Phase 8 is successful if:

1. ✅ HTML reports generate with professional styling
2. ✅ HTML reports include all sections (summary, issues, pages, checklist)
3. ✅ CSV exports contain all issue data in proper format
4. ✅ Reports work for scans with varying amounts of data
5. ✅ CLI export commands work for all formats (JSON, HTML, CSV)
6. ✅ API endpoints return correct content types
7. ✅ Error handling works correctly
8. ✅ HTML reports are responsive and print-friendly
9. ✅ Reports are accessible (WCAG compliant)
10. ✅ No crashes or data loss during report generation

## Next Steps

After Phase 8 testing:

- **Phase 9** (Optional): PDF report generation
- **Phase 10** (Optional): Report scheduling and email delivery
- **Enhancements**:
  - Chart visualizations in HTML reports
  - Trend analysis over multiple scans
  - Custom report templates
  - Report comparison views

## Example Test Session

```bash
# 1. Setup
python main_v2.py &  # Start API server
python cli_v2.py auth login --email user@example.com --password Pass123

# 2. Create test data
PROJECT_ID=$(python cli_v2.py project create "Test" "https://example.com" | grep "ID:" | awk '{print $2}')
SCAN_ID=$(python cli_v2.py scan start $PROJECT_ID --max-pages 5 --wait | grep "Scan ID:" | awk '{print $3}')

# 3. Test reports
python cli_v2.py report view $SCAN_ID
python cli_v2.py report export $SCAN_ID -o test_report.json -f json
python cli_v2.py report export $SCAN_ID -o test_report.html -f html
python cli_v2.py report export $SCAN_ID -o test_report.csv -f csv

# 4. Open HTML report
open test_report.html

# 5. Verify files
ls -lh test_report.*
file test_report.*

# 6. Cleanup
rm test_report.*
```

## Report Quality Checks

For each generated report, verify:

### Data Accuracy
- [ ] All scanned pages are included
- [ ] Issue counts match actual issues
- [ ] Scores are calculated correctly
- [ ] WCAG criteria mappings are correct

### Completeness
- [ ] No missing sections
- [ ] All issue details present
- [ ] Help URLs and descriptions included
- [ ] Timestamps are accurate

### Usability
- [ ] Easy to navigate and find information
- [ ] Clear visual hierarchy
- [ ] Actionable recommendations
- [ ] Professional appearance suitable for clients

### Technical Quality
- [ ] Valid HTML/CSS
- [ ] Valid CSV format
- [ ] Valid JSON structure
- [ ] No broken links or images
- [ ] Proper character encoding
