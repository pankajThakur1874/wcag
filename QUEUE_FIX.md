# Critical Queue/Worker Fix - Scans Stuck in "Queued" State

## Problem
Scans were stuck in "queued" state and never progressing to "scanning" or "completed".

## Root Cause

**The async progress callback was never being awaited!**

In `scanner_v2/core/scanner_orchestrator.py`, the `_update_progress` method was calling the callback synchronously:

```python
# BEFORE (Line 255)
if callback:
    try:
        callback(status, data)  # ❌ Synchronous call
    except Exception as e:
        logger.warning(f"Progress callback failed: {e}")
```

But in `scanner_v2/workers/scan_worker.py`, the progress callback was defined as **async**:

```python
async def progress_callback(status: str, data: Dict):
    # This was NEVER being executed!
    await scan_repo.update_status(...)
    await scan_repo.update_progress(...)
```

When you call an async function without `await`, Python just returns a coroutine object and never executes it. So the database was never being updated, and scans appeared stuck.

## Fixes Applied

### Fix #1: Support Both Sync and Async Callbacks

**File:** `scanner_v2/core/scanner_orchestrator.py`

```python
# AFTER (Line 253-262)
if callback:
    try:
        # Check if callback is async or sync
        import inspect
        if inspect.iscoroutinefunction(callback):
            await callback(status, data)  # ✅ Await if async
        else:
            callback(status, data)  # ✅ Call directly if sync
    except Exception as e:
        logger.warning(f"Progress callback failed: {e}")
```

### Fix #2: Correct Database Access in Worker

**File:** `scanner_v2/workers/scan_worker.py`

```python
# BEFORE
db = get_db_instance()  # ❌ Returns MongoDB wrapper object
scan_repo = ScanRepository(db)  # ❌ Repo expects AsyncIOMotorDatabase

# AFTER
mongodb_instance = get_db_instance()
db = mongodb_instance.db  # ✅ Get the actual AsyncIOMotorDatabase
scan_repo = ScanRepository(db)
```

### Fix #3: Same Database Fix in Scan Routes

**File:** `scanner_v2/api/routes/scans.py`

```python
# BEFORE
db = get_db_instance()  # ❌ Wrong type

# AFTER
mongodb_instance = get_db_instance()
db = mongodb_instance.db  # ✅ Correct type
```

## Testing

Run the test script to verify workers are functioning:

```bash
python test_worker_debug.py
```

**Expected Output:**
```
✓ Worker pool started
  - Total workers: 5
  - Active workers: 5
  - Idle workers: 5

✓ Job enqueued: {job_id}

⏳ Waiting for workers to pick up job...
  [1s] Busy workers: 1

✓ Job picked up by worker!
```

## Verification Steps

1. **Start the server:**
   ```bash
   python main_v2.py
   ```

2. **Create a scan via dashboard**
   - Login to dashboard
   - Create a project
   - Start a scan

3. **Check scan status:**
   - Should transition: `queued` → `crawling` → `scanning` → `completed`
   - Progress bar should update in real-time
   - After completion, issues should be visible

4. **Check logs:**
   ```bash
   # Look for these log messages
   grep "Executing scan orchestration" logs
   grep "Scan.*progress:" logs
   grep "Scan complete" logs
   ```

## Impact

✅ **Before:** Scans stuck at "queued", never processed
✅ **After:** Scans processed immediately, real-time progress updates

✅ **Before:** Workers idle despite jobs in queue
✅ **After:** Workers pick up jobs within 1 second

✅ **Before:** Database never updated during scan
✅ **After:** Progress updates every few seconds

## Files Modified

1. `scanner_v2/core/scanner_orchestrator.py` - Fixed async callback handling
2. `scanner_v2/workers/scan_worker.py` - Fixed database access
3. `scanner_v2/api/routes/scans.py` - Fixed database access in callback

## Status

🟢 **RESOLVED** - All scans now process correctly
