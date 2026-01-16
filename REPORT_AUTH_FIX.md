# Report Download Authentication Fix

## Problem

When clicking on report download buttons, users got "Not Authenticated" errors.

## Root Cause

The `downloadReport()` method in the API client was using `window.open()`:

```javascript
downloadReport(scanId, format) {
    window.open(`${this.baseURL}/scans/${scanId}/reports/${format}`, '_blank');
}
```

**Issue:** `window.open()` opens a new browser window/tab but **does NOT send authentication headers**. The JWT token stored in localStorage is not automatically included in the request, so the API sees it as an unauthenticated request and returns a 401 error.

## Fix Applied

### Changed Download Method to Use Fetch with Auth Headers

**File:** `templates/dashboard_v2.html`

#### Before (Broken):
```javascript
downloadReport(scanId, format) {
    window.open(`${this.baseURL}/scans/${scanId}/reports/${format}`, '_blank');
    // ❌ No auth headers sent
}
```

#### After (Fixed):
```javascript
async downloadReport(scanId, format, openInNewTab = false) {
    try {
        // ✅ Include auth token in headers
        const headers = {
            'Authorization': `Bearer ${this.token}`
        };

        const response = await fetch(`${this.baseURL}/scans/${scanId}/reports/${format}`, {
            headers
        });

        if (!response.ok) {
            throw new Error('Failed to download report');
        }

        // Get content and create blob
        let blob, filename;

        if (format === 'json') {
            const data = await response.json();
            blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            filename = `wcag_report_${scanId}.json`;
        } else if (format === 'html') {
            const html = await response.text();
            blob = new Blob([html], { type: 'text/html' });
            filename = `wcag_report_${scanId}.html`;

            // For HTML, can open in new tab
            if (openInNewTab) {
                const url = window.URL.createObjectURL(blob);
                window.open(url, '_blank');
                setTimeout(() => window.URL.revokeObjectURL(url), 100);
                return true;
            }
        } else if (format === 'csv') {
            const csv = await response.text();
            blob = new Blob([csv], { type: 'text/csv' });
            filename = `wcag_report_${scanId}.csv`;
        }

        // Trigger download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        return true;
    } catch (error) {
        console.error('Download error:', error);
        throw error;
    }
}
```

### How It Works Now

1. **Fetch with Auth:** Uses `fetch()` with `Authorization: Bearer <token>` header
2. **Get Content:** Receives the report content from API
3. **Create Blob:** Converts content to a Blob object
4. **Trigger Download:** Creates a temporary download link and clicks it
5. **Cleanup:** Removes the temporary link and revokes the blob URL

### Added View in Browser Feature

For HTML reports, added a "View HTML" button that opens the report in a new tab instead of downloading:

```javascript
// Button options for HTML report
<button onclick="viewReport('${scanId}', 'html')">👁️ View HTML</button>
<button onclick="downloadReport('${scanId}', 'html')">⬇️ Download HTML</button>

// View function
async function viewReport(scanId, format) {
    await api.downloadReport(scanId, format, true);  // openInNewTab=true
}
```

### Updated UI Functions

```javascript
// Download function with error handling
async function downloadReport(scanId, format) {
    try {
        showToast(`Preparing ${format.toUpperCase()} report...`, 'info');
        await api.downloadReport(scanId, format, false);
        showToast(`${format.toUpperCase()} report downloaded successfully!`, 'success');
    } catch (error) {
        console.error('Download failed:', error);
        showToast(`Failed to download ${format.toUpperCase()} report. Please try again.`, 'error');
    }
}

// View function for HTML reports
async function viewReport(scanId, format) {
    try {
        showToast(`Opening ${format.toUpperCase()} report in new tab...`, 'info');
        await api.downloadReport(scanId, format, true);
    } catch (error) {
        console.error('View failed:', error);
        showToast(`Failed to open ${format.toUpperCase()} report. Please try again.`, 'error');
    }
}
```

## Benefits

✅ **Authentication Works:** JWT token properly included in requests
✅ **Better UX:** Progress toasts and error messages
✅ **View HTML:** Can view HTML reports in browser without downloading
✅ **Proper Downloads:** All formats download with correct filenames
✅ **Error Handling:** Clear error messages if download fails

## Testing

1. **Login to dashboard**
2. **Go to Reports tab**
3. **Select a completed scan**
4. **Click download buttons:**
   - 📄 Download JSON - Should download `wcag_report_{scanId}.json`
   - 👁️ View HTML - Should open formatted report in new tab
   - ⬇️ Download HTML - Should download `wcag_report_{scanId}.html`
   - 📊 Download CSV - Should download `wcag_report_{scanId}.csv`

**Expected:** All downloads work without authentication errors

## Files Modified

1. ✅ `templates/dashboard_v2.html` - Fixed downloadReport() method and added viewReport()

## Technical Details

### Why Fetch Instead of window.open?

| Method | Auth Headers | Control | Download Naming |
|--------|-------------|---------|-----------------|
| `window.open()` | ❌ No | None | Browser default |
| `fetch()` + Blob | ✅ Yes | Full | Custom filename |

### Blob Download Pattern

```javascript
// 1. Create blob from content
const blob = new Blob([content], { type: 'text/csv' });

// 2. Create temporary URL
const url = window.URL.createObjectURL(blob);

// 3. Create link and trigger download
const a = document.createElement('a');
a.href = url;
a.download = filename;
document.body.appendChild(a);
a.click();

// 4. Cleanup
window.URL.revokeObjectURL(url);
document.body.removeChild(a);
```

## Status

🟢 **RESOLVED** - Report downloads now work with authentication
