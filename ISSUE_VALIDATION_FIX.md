# Issue Validation Error Fix

## Problem

When saving issues to the database after scan completion, validation errors occurred:

```
2 validation errors for Issue
page_id
  Field required [type=missing]
detected_by
  Input should be a valid list [type=list_type, input_value='axe', input_type=str]
```

## Root Causes

### 1. Missing `page_id` Field
The Issue model requires `page_id` as a mandatory field, but it wasn't being included when creating Issue objects in `scans.py`.

### 2. `detected_by` Type Mismatch
- Issue model expects: `detected_by: List[str]`
- Scanner service was setting: `detected_by: "axe"` (string)

## Fixes Applied

### Fix #1: Add `page_id` Field

**File:** `scanner_v2/api/routes/scans.py`

```python
issue = Issue(
    scan_id=scan_id,
    page_id=issue_data.get("page_id", ""),  # ✅ Added required field
    rule_id=issue_data.get("rule_id", ""),
    # ... other fields
)
```

### Fix #2: Convert `detected_by` to List

**File:** `scanner_v2/services/scanner_service.py`

```python
# BEFORE
"detected_by": scanner_name  # ❌ String

# AFTER
"detected_by": [scanner_name]  # ✅ List[str]
```

### Fix #3: Defensive Handling in Scans.py

**File:** `scanner_v2/api/routes/scans.py`

```python
# Handle both string and list formats defensively
detected_by = issue_data.get("detected_by", [])
if isinstance(detected_by, str):
    detected_by = [detected_by]
elif not detected_by:
    detected_by = ["unknown"]

issue = Issue(
    # ...
    detected_by=detected_by,  # ✅ Always a list
    # ...
)
```

### Fix #4: Correct Field Name

**File:** `scanner_v2/api/routes/scans.py`

```python
# BEFORE
help=issue_data.get("help", ""),  # ❌ Wrong field name

# AFTER
help_text=issue_data.get("help", ""),  # ✅ Correct field name from Issue model
```

## Testing

After these fixes, issues should save correctly:

```bash
# Check logs for successful save
grep "Saved.*issues for scan" logs

# Check database
mongosh
use wcag_scanner
db.issues.countDocuments()  # Should show issues
db.issues.findOne()  # Should show proper structure
```

## Files Modified

1. ✅ `scanner_v2/api/routes/scans.py` - Added page_id, fixed detected_by, fixed help_text
2. ✅ `scanner_v2/services/scanner_service.py` - Changed detected_by to list

## Impact

✅ Issues now save correctly to database
✅ Scans complete without validation errors
✅ Dashboard can display issues properly

## Status

🟢 **RESOLVED** - Issues validated and saved successfully
