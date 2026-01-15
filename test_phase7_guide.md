# Phase 7 Test Guide: TUI Dashboard

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

4. **Test Data** (optional but recommended):
   ```bash
   # Create some projects
   python cli_v2.py project create "Site 1" "https://example.com"
   python cli_v2.py project create "Site 2" "https://test.com"

   # Start some scans
   python cli_v2.py scan start PROJECT_ID1 --max-pages 5
   python cli_v2.py scan start PROJECT_ID2 --max-pages 3
   ```

## Running the Dashboard

```bash
python cli_v2.py dashboard
```

## Dashboard Features to Test

### 1. Initial Display
- ✅ Dashboard loads successfully
- ✅ Statistics panel shows at the top
- ✅ Scans table displays in the left panel
- ✅ Projects table displays in the right panel
- ✅ Header shows "WCAGDashboardApp"
- ✅ Footer shows keyboard shortcuts

### 2. Statistics Panel
Should display:
- Number of projects
- Total scans count
- Total issues count
- Scan status breakdown (completed, scanning, failed)

### 3. Scans Table
Columns should show:
- ID (first 8 chars)
- Project ID (first 8 chars)
- Status (color-coded: green=completed, yellow=scanning, red=failed, blue=queued)
- Progress (scanned/total pages)
- Issues count
- Compliance score

### 4. Projects Table
Columns should show:
- ID (first 8 chars)
- Name (truncated to 30 chars)

### 5. Keyboard Shortcuts

Test each binding:

- **q** - Quit the dashboard
  - Press 'q' → Dashboard should exit cleanly

- **r** - Refresh data
  - Press 'r' → Should show "Refreshing data..." notification
  - Data should update from API

- **s** - Scans view
  - Press 's' → Should show "Scans view" notification

- **p** - Projects view
  - Press 'p' → Should show "Projects view" notification

- **d** - Dashboard view
  - Press 'd' → Should show "Dashboard view" notification

### 6. Auto-Refresh

- Dashboard should automatically refresh every 5 seconds
- Watch for status changes in running scans
- Progress values should update
- New scans/projects should appear

### 7. Mouse Interaction

- Click on "Refresh (r)" button → Should refresh data
- Click on "Quit (q)" button → Should exit dashboard
- Click on table rows → Should highlight row

### 8. Data Updates

Test real-time updates:

1. With dashboard running, in another terminal:
   ```bash
   python cli_v2.py scan start PROJECT_ID --max-pages 3
   ```

2. Watch the dashboard:
   - New scan should appear in table (after auto-refresh)
   - Status should change from queued → scanning → completed
   - Progress numbers should update
   - Statistics should update

### 9. Error Handling

Test error scenarios:

1. **No Authentication**:
   ```bash
   python cli_v2.py auth logout
   python cli_v2.py dashboard
   ```
   - Should show error notification or empty tables

2. **API Server Down**:
   - Stop API server
   - Dashboard should show error notification
   - Should not crash

3. **Network Issues**:
   - Disconnect network briefly
   - Dashboard should handle gracefully

### 10. Visual Appearance

Check styling:
- ✅ Tables have borders
- ✅ Status colors are visible
- ✅ Stats panel has distinct background
- ✅ Text is readable
- ✅ Layout is responsive to terminal size

## Expected Behavior

### On Launch
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ WCAGDashboardApp                                                    ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Dashboard Statistics                                                ┃
┃                                                                      ┃
┃ Projects: 2  |  Total Scans: 5  |  Total Issues: 123               ┃
┃                                                                      ┃
┃ Scans: 3 Completed  |  1 Scanning  |  1 Failed                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Recent Scans                        │ Projects
┏━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┓  │ ┏━━━━━━━━┳━━━━━━━━━━━━┓
┃ ID     ┃ Project ┃ Status     ┃  │ ┃ ID     ┃ Name       ┃
┡━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━┩  │ ┡━━━━━━━━╇━━━━━━━━━━━━┩
│ abc123 │ def456  │ completed  │  │ │ def456 │ Site 1     │
│ xyz789 │ def456  │ scanning   │  │ │ ghi012 │ Site 2     │
└────────┴─────────┴────────────┘  │ └────────┴────────────┘

 Refresh (r)   Quit (q)

 q Quit  r Refresh  s Scans  p Projects  d Dashboard
```

### On Refresh
```
 Refreshing data...
 [Wait ~1 second]
 Data refreshed
```

### On Quit
- Dashboard closes cleanly
- Returns to terminal prompt
- No error messages

## Test Results Checklist

- [ ] Dashboard launches successfully
- [ ] Statistics panel displays correctly
- [ ] Scans table shows data
- [ ] Projects table shows data
- [ ] Status colors are correct
- [ ] Keyboard shortcut 'q' quits
- [ ] Keyboard shortcut 'r' refreshes
- [ ] Auto-refresh works (every 5 seconds)
- [ ] Mouse clicks work on buttons
- [ ] Table rows are selectable
- [ ] Real-time updates appear
- [ ] New scans show up after auto-refresh
- [ ] Scan status changes are reflected
- [ ] Progress numbers update
- [ ] No crashes or errors
- [ ] Clean exit with 'q'

## Common Issues

### Issue: "No module named 'textual'"
**Solution**:
```bash
pip install textual
```

### Issue: Dashboard shows empty tables
**Solution**:
- Make sure you're logged in: `python cli_v2.py auth login`
- Check API server is running
- Create test data with project/scan commands

### Issue: "Not authenticated" error
**Solution**:
```bash
python cli_v2.py auth login --email user@example.com --password Pass123
```

### Issue: Data not updating
**Solution**:
- Press 'r' to force refresh
- Check API server logs
- Wait for auto-refresh (5 seconds)

## Success Criteria

Phase 7 is successful if:
1. ✅ Dashboard launches without errors
2. ✅ All data displays correctly
3. ✅ Auto-refresh updates data every 5 seconds
4. ✅ Keyboard shortcuts work
5. ✅ Real-time scan status changes appear
6. ✅ Dashboard exits cleanly with 'q'
7. ✅ No crashes during normal operation

## Next Steps

After Phase 7 testing:
- **Phase 8**: HTML/CSV report generation
- Enhanced TUI features (detail views, filters)
- Additional screens for issues and reports
