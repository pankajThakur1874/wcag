# Reports Section UI Fix

## Problem

The Reports tab in the dashboard V2 was not showing any reports or download options. It only displayed a static empty state message saying "Select a scan to download reports" but had no functionality to actually select or download reports.

## Root Cause

The dashboard had the reports API client method (`downloadReport()`) but was missing:
1. UI to select a completed scan
2. UI to display download buttons
3. Function to populate the reports section
4. Logic to call the function when switching to reports tab

## Fix Applied

### Added Reports UI Functionality

**File:** `templates/dashboard_v2.html`

#### 1. Updated Tab Switching

```javascript
function switchTab(tabName) {
    // ... existing code ...

    if (tabName === 'issues') {
        populateScanFilter();
    } else if (tabName === 'reports') {
        loadReportsSection();  // ✅ Added this
    }
}
```

#### 2. Added `loadReportsSection()` Function

```javascript
function loadReportsSection() {
    const content = document.getElementById('reportsContent');
    const completedScans = appState.scans.filter(s => s.status.toLowerCase() === 'completed');

    if (!completedScans.length) {
        // Show empty state if no completed scans
        content.innerHTML = `...`;
        return;
    }

    // Show dropdown to select a scan
    content.innerHTML = `
        <select id="reportScanSelect" onchange="showReportDownloads(this.value)">
            <option value="">Choose a scan...</option>
            ${completedScans.map(scan => `<option value="${scan.id}">...</option>`)}
        </select>
        <div id="reportDownloads"></div>
    `;
}
```

#### 3. Added `showReportDownloads()` Function

```javascript
function showReportDownloads(scanId) {
    if (!scanId) {
        return;
    }

    const scan = appState.scans.find(s => s.id === scanId);
    const project = appState.projects.find(p => p.id === scan.project_id);

    // Display scan info and download buttons
    container.innerHTML = `
        <div>
            <h3>Download Report</h3>

            <!-- Scan Summary -->
            <div>Project: ${project.name}</div>
            <div>Scan completed: ${scan.completed_at}</div>
            <div>Total Issues: ${scan.summary.total_issues}</div>

            <!-- Download Buttons -->
            <button onclick="downloadReport('${scanId}', 'json')">
                📄 Download JSON Report
            </button>
            <button onclick="downloadReport('${scanId}', 'html')">
                🌐 Download HTML Report
            </button>
            <button onclick="downloadReport('${scanId}', 'csv')">
                📊 Download CSV Report
            </button>
        </div>
    `;
}
```

#### 4. Added `downloadReport()` Helper Function

```javascript
function downloadReport(scanId, format) {
    api.downloadReport(scanId, format);
    showToast(`Downloading ${format.toUpperCase()} report...`, 'success');
}
```

## Features

### Report Selection
- Dropdown shows all completed scans
- Format: "Project Name - Completion Date"
- Only completed scans are available

### Scan Summary Display
When a scan is selected, shows:
- Project name
- Scan completion date
- Total issues found
- Compliance score (if available)

### Download Buttons
Three download options:
1. **JSON** - Machine-readable format for integrations
2. **HTML** - Formatted report for viewing in browser
3. **CSV** - Spreadsheet format for Excel/Google Sheets

### Empty States
- If no completed scans: "No completed scans" message
- If no scan selected: No download buttons shown

## How It Works

1. User clicks "Reports" tab
2. `loadReportsSection()` is called automatically
3. Dropdown is populated with completed scans
4. User selects a scan from dropdown
5. `showReportDownloads()` displays scan info and buttons
6. User clicks download button
7. Report opens in new tab/downloads

## API Endpoints Used

The UI calls these existing API endpoints:

```javascript
// JSON Report
GET /api/v1/scans/{scan_id}/reports/json

// HTML Report
GET /api/v1/scans/{scan_id}/reports/html

// CSV Report
GET /api/v1/scans/{scan_id}/reports/csv
```

All endpoints:
- Require authentication (JWT token)
- Check scan ownership
- Return comprehensive report data

## Testing

1. **With no completed scans:**
   - Go to Reports tab
   - Should see: "No completed scans" message

2. **With completed scans:**
   - Go to Reports tab
   - Should see: Dropdown with completed scans
   - Select a scan
   - Should see: Scan info and 3 download buttons

3. **Download reports:**
   - Click "Download JSON Report"
   - Should open new tab with JSON data
   - Click "Download HTML Report"
   - Should open new tab with formatted HTML
   - Click "Download CSV Report"
   - Should download CSV file

## Files Modified

1. ✅ `templates/dashboard_v2.html` - Added complete reports UI functionality

## Impact

✅ Reports section now fully functional
✅ Users can download reports in 3 formats
✅ Clear UI with scan selection and summary
✅ Proper empty states

## Status

🟢 **RESOLVED** - Reports section now displays and works correctly
