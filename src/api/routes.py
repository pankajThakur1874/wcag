"""FastAPI routes for WCAG Scanner API."""

from typing import Optional
from uuid import uuid4
import asyncio

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl, Field

from src.core import ResultsAggregator, ReportGenerator
from src.models import ScanResult, ScanStatus
from src.scanners import SCANNERS
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["scans"])

# In-memory storage for scan results (use Redis/DB in production)
_scan_results: dict[str, ScanResult] = {}
_scan_tasks: dict[str, asyncio.Task] = {}


class ScanRequest(BaseModel):
    """Request model for starting a scan."""
    url: HttpUrl = Field(..., description="URL to scan")
    tools: Optional[list[str]] = Field(None, description="Tools to use (default: all)")
    wcag_level: str = Field("AA", description="WCAG conformance level")


class ScanResponse(BaseModel):
    """Response model for scan initiation."""
    scan_id: str
    status: str
    message: str


class ScanStatusResponse(BaseModel):
    """Response model for scan status."""
    scan_id: str
    status: str
    url: str
    progress: Optional[str] = None


@router.post("/scan", response_model=ScanResponse)
async def start_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks
) -> ScanResponse:
    """
    Start a new accessibility scan.

    Returns a scan_id that can be used to check status and get results.
    """
    # Validate tools
    if request.tools:
        invalid_tools = set(request.tools) - set(SCANNERS.keys())
        if invalid_tools:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tools: {invalid_tools}. Available: {list(SCANNERS.keys())}"
            )

    scan_id = str(uuid4())

    # Create initial result
    result = ScanResult(
        scan_id=scan_id,
        url=str(request.url),
        status=ScanStatus.PENDING
    )
    _scan_results[scan_id] = result

    # Start scan in background
    background_tasks.add_task(_run_scan, scan_id, str(request.url), request.tools)

    return ScanResponse(
        scan_id=scan_id,
        status="pending",
        message=f"Scan started for {request.url}"
    )


async def _run_scan(scan_id: str, url: str, tools: Optional[list[str]]):
    """Run scan in background."""
    try:
        _scan_results[scan_id].status = ScanStatus.RUNNING

        aggregator = ResultsAggregator(tools=tools)
        result = await aggregator.scan(url)
        result.scan_id = scan_id

        _scan_results[scan_id] = result

    except Exception as e:
        logger.error(f"Scan {scan_id} failed: {e}")
        _scan_results[scan_id].status = ScanStatus.FAILED
        _scan_results[scan_id].error = str(e)


@router.get("/scan/{scan_id}", response_model=None)
async def get_scan_result(scan_id: str):
    """
    Get scan result by ID.

    Returns the full scan result once completed, or status if still running.
    """
    if scan_id not in _scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")

    result = _scan_results[scan_id]

    if result.status in [ScanStatus.PENDING, ScanStatus.RUNNING]:
        return ScanStatusResponse(
            scan_id=scan_id,
            status=result.status.value,
            url=result.url,
            progress="Scanning in progress..."
        )

    return result


@router.get("/scan/{scan_id}/report", response_class=HTMLResponse)
async def get_scan_report(scan_id: str, format: str = "html"):
    """
    Get formatted report for a completed scan.

    Args:
        scan_id: Scan ID
        format: Report format (html or json)
    """
    if scan_id not in _scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")

    result = _scan_results[scan_id]

    if result.status != ScanStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Scan not completed. Status: {result.status.value}"
        )

    generator = ReportGenerator()

    if format == "json":
        return generator.to_json(result)

    return generator.to_html(result)


@router.get("/scans")
async def list_scans(limit: int = 10):
    """List recent scans."""
    scans = list(_scan_results.values())[-limit:]
    return [
        {
            "scan_id": s.scan_id,
            "url": s.url,
            "status": s.status.value,
            "timestamp": s.timestamp.isoformat(),
            "score": s.scores.overall if s.status == ScanStatus.COMPLETED else None,
            "violations": s.summary.total_violations if s.status == ScanStatus.COMPLETED else None
        }
        for s in reversed(scans)
    ]


@router.get("/tools")
async def list_tools():
    """List available scanning tools."""
    return {
        "tools": list(SCANNERS.keys()),
        "descriptions": {
            "axe": "axe-core accessibility engine",
            "pa11y": "Pa11y automated accessibility testing",
            "lighthouse": "Google Lighthouse accessibility audits",
            "html_validator": "HTML structure validation",
            "contrast": "Color contrast checker"
        }
    }


@router.delete("/scan/{scan_id}")
async def delete_scan(scan_id: str):
    """Delete a scan result."""
    if scan_id not in _scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")

    del _scan_results[scan_id]
    return {"message": f"Scan {scan_id} deleted"}
