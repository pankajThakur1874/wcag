"""FastAPI routes for WCAG Scanner API."""

from typing import Optional
from uuid import uuid4
import asyncio

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, HttpUrl, Field

from src.core import ResultsAggregator, ReportGenerator, SiteScanner, SiteScanResult
from src.models import ScanResult, ScanStatus
from src.scanners import SCANNERS
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["scans"])

# In-memory storage for scan results (use Redis/DB in production)
_scan_results: dict[str, ScanResult] = {}
_scan_tasks: dict[str, asyncio.Task] = {}
_site_scan_results: dict[str, dict] = {}  # Site-wide scan results


class ScanRequest(BaseModel):
    """Request model for starting a scan."""
    url: HttpUrl = Field(..., description="URL to scan")
    tools: Optional[list[str]] = Field(None, description="Tools to use (default: all)")
    wcag_level: str = Field("AA", description="WCAG conformance level")
    site_wide: bool = Field(False, description="Scan entire site (crawl and scan all pages)")
    max_pages: int = Field(20, description="Maximum pages to scan (site-wide only)")
    max_depth: int = Field(2, description="Maximum crawl depth (site-wide only)")


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
    Set site_wide=true to crawl and scan all pages on the website.
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

    if request.site_wide:
        # Site-wide scan
        _site_scan_results[scan_id] = {
            "scan_id": scan_id,
            "base_url": str(request.url),
            "status": "pending",
            "progress": {"phase": "starting", "current": 0, "total": 0, "message": "Initializing..."},
            "result": None
        }

        background_tasks.add_task(
            _run_site_scan,
            scan_id,
            str(request.url),
            request.tools,
            request.max_pages,
            request.max_depth
        )

        return ScanResponse(
            scan_id=scan_id,
            status="pending",
            message=f"Site-wide scan started for {request.url} (max {request.max_pages} pages)"
        )
    else:
        # Single page scan
        result = ScanResult(
            scan_id=scan_id,
            url=str(request.url),
            status=ScanStatus.PENDING
        )
        _scan_results[scan_id] = result

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


async def _run_site_scan(
    scan_id: str,
    url: str,
    tools: Optional[list[str]],
    max_pages: int,
    max_depth: int
):
    """Run site-wide scan in background."""
    try:
        _site_scan_results[scan_id]["status"] = "running"

        scanner = SiteScanner(
            max_pages=max_pages,
            max_depth=max_depth,
            tools=tools,
            concurrent_scans=2
        )

        def progress_callback(phase: str, current: int, total: int, message: str):
            _site_scan_results[scan_id]["progress"] = {
                "phase": phase,
                "current": current,
                "total": total,
                "message": message
            }

        scanner.set_progress_callback(progress_callback)

        result = await scanner.scan_site(url)
        result.scan_id = scan_id

        _site_scan_results[scan_id]["status"] = result.status.value
        _site_scan_results[scan_id]["result"] = result.to_dict()

    except Exception as e:
        logger.error(f"Site scan {scan_id} failed: {e}")
        _site_scan_results[scan_id]["status"] = "failed"
        _site_scan_results[scan_id]["error"] = str(e)


@router.get("/scan/{scan_id}", response_model=None)
async def get_scan_result(scan_id: str):
    """
    Get scan result by ID.

    Returns the full scan result once completed, or status if still running.
    Works for both single-page and site-wide scans.
    """
    # Check if it's a site-wide scan
    if scan_id in _site_scan_results:
        site_result = _site_scan_results[scan_id]

        if site_result["status"] in ["pending", "running"]:
            return {
                "scan_id": scan_id,
                "status": site_result["status"],
                "site_wide": True,
                "url": site_result["base_url"],
                "progress": site_result.get("progress", {})
            }

        if site_result["status"] == "failed":
            return {
                "scan_id": scan_id,
                "status": "failed",
                "site_wide": True,
                "error": site_result.get("error", "Unknown error")
            }

        # Completed - return full result
        result = site_result.get("result", {})
        result["site_wide"] = True
        return result

    # Check if it's a single-page scan
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


@router.get("/scan/{scan_id}/download")
async def download_report(scan_id: str, format: str = "html"):
    """
    Download report as a file.

    Args:
        scan_id: Scan ID
        format: Report format (html or json)
    """
    from urllib.parse import urlparse
    from datetime import datetime
    import json

    # Check if it's a site-wide scan
    if scan_id in _site_scan_results:
        site_result = _site_scan_results[scan_id]

        if site_result["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Scan not completed. Status: {site_result['status']}"
            )

        result_data = site_result.get("result", {})
        domain = urlparse(result_data.get("base_url", "")).netloc.replace(".", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            content = json.dumps(result_data, indent=2, default=str)
            filename = f"wcag_site_report_{domain}_{timestamp}.json"
            media_type = "application/json"
        else:
            content = _generate_site_html_report(result_data)
            filename = f"wcag_site_report_{domain}_{timestamp}.html"
            media_type = "text/html"

        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    # Single page scan
    if scan_id not in _scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")

    result = _scan_results[scan_id]

    if result.status != ScanStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Scan not completed. Status: {result.status.value}"
        )

    generator = ReportGenerator()

    domain = urlparse(result.url).netloc.replace(".", "_")
    timestamp = result.timestamp.strftime("%Y%m%d_%H%M%S")

    if format == "json":
        content = generator.to_json(result)
        filename = f"wcag_report_{domain}_{timestamp}.json"
        media_type = "application/json"
    else:
        content = generator.to_html(result)
        filename = f"wcag_report_{domain}_{timestamp}.html"
        media_type = "text/html"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


def _generate_site_html_report(data: dict) -> str:
    """Generate HTML report for site-wide scan."""
    summary = data.get("summary", {})
    page_results = data.get("page_results", [])
    impact = summary.get("by_impact", {})

    pages_html = ""
    for page in page_results:
        score_class = "good" if page["score"] >= 90 else ("warning" if page["score"] >= 70 else "bad")
        pages_html += f"""
        <tr>
            <td><a href="{page['url']}" target="_blank">{page['url']}</a></td>
            <td class="{score_class}">{page['score']}%</td>
            <td>{page['violations_count']}</td>
            <td>{page['rules_passed']}/{page['rules_checked']}</td>
        </tr>
        """

    worst_pages_html = ""
    for page in summary.get("worst_pages", []):
        worst_pages_html += f"""
        <li><strong>{page['url']}</strong> - {page['violations']} issues (Score: {page['score']}%)</li>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Site-Wide WCAG Report - {data.get('base_url', 'Unknown')}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #1f2937; border-bottom: 3px solid #6366f1; padding-bottom: 15px; }}
            h2 {{ color: #374151; margin-top: 30px; }}
            .score-card {{ display: flex; gap: 30px; margin: 20px 0; flex-wrap: wrap; }}
            .score {{ text-align: center; padding: 20px; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; border-radius: 12px; min-width: 150px; }}
            .score-value {{ font-size: 3rem; font-weight: bold; }}
            .stat {{ text-align: center; padding: 15px; background: #f3f4f6; border-radius: 8px; min-width: 100px; }}
            .stat-value {{ font-size: 1.5rem; font-weight: bold; }}
            .stat.critical .stat-value {{ color: #ef4444; }}
            .stat.serious .stat-value {{ color: #f97316; }}
            .stat.moderate .stat-value {{ color: #f59e0b; }}
            .stat.minor .stat-value {{ color: #10b981; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
            th {{ background: #f9fafb; font-weight: 600; }}
            .good {{ color: #059669; font-weight: bold; }}
            .warning {{ color: #d97706; font-weight: bold; }}
            .bad {{ color: #dc2626; font-weight: bold; }}
            .summary-box {{ background: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            ul {{ line-height: 1.8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Site-Wide WCAG Accessibility Report</h1>
            <p><strong>Website:</strong> {data.get('base_url', 'Unknown')}</p>
            <p><strong>Scan Date:</strong> {data.get('timestamp', 'Unknown')}</p>
            <p><strong>Duration:</strong> {data.get('duration_seconds', 0)} seconds</p>

            <div class="score-card">
                <div class="score">
                    <div class="score-value">{data.get('overall_score', 0)}%</div>
                    <div>Overall Score</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{data.get('pages_scanned', 0)}</div>
                    <div>Pages Scanned</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{data.get('total_rules_passed', 0)}/{data.get('total_rules_checked', 0)}</div>
                    <div>Tests Passed</div>
                </div>
                <div class="stat critical">
                    <div class="stat-value">{impact.get('critical', 0)}</div>
                    <div>Critical</div>
                </div>
                <div class="stat serious">
                    <div class="stat-value">{impact.get('serious', 0)}</div>
                    <div>Serious</div>
                </div>
                <div class="stat moderate">
                    <div class="stat-value">{impact.get('moderate', 0)}</div>
                    <div>Moderate</div>
                </div>
                <div class="stat minor">
                    <div class="stat-value">{impact.get('minor', 0)}</div>
                    <div>Minor</div>
                </div>
            </div>

            <div class="summary-box">
                <strong>Summary:</strong> Found <strong>{data.get('unique_violations_count', 0)}</strong> unique violations
                across <strong>{data.get('pages_scanned', 0)}</strong> pages
                ({data.get('total_violations_count', 0)} total occurrences).
                Average page score: <strong>{summary.get('average_score', 0)}%</strong>
            </div>

            <h2>Pages with Most Issues</h2>
            <ul>
                {worst_pages_html or '<li>No significant issues found</li>'}
            </ul>

            <h2>All Pages Scanned</h2>
            <table>
                <thead>
                    <tr>
                        <th>URL</th>
                        <th>Score</th>
                        <th>Violations</th>
                        <th>Tests Passed</th>
                    </tr>
                </thead>
                <tbody>
                    {pages_html}
                </tbody>
            </table>

            <p style="margin-top: 30px; color: #666; text-align: center;">
                Generated by WCAG Accessibility Scanner
            </p>
        </div>
    </body>
    </html>
    """


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
            "contrast": "Color contrast checker (WCAG AA/AAA)",
            "keyboard": "Keyboard accessibility testing",
            "aria": "ARIA roles and attributes validation",
            "forms": "Form accessibility checker",
            "seo": "SEO and meta accessibility",
            "link_text": "Link text quality (vague links)",
            "image_alt": "Image alt text quality",
            "media": "Video/audio accessibility",
            "touch_target": "Touch target size checker",
            "readability": "Content readability analysis",
            "interactive": "Interactive elements (tabs, modals, accordions, dropdowns)"
        }
    }


@router.delete("/scan/{scan_id}")
async def delete_scan(scan_id: str):
    """Delete a scan result."""
    if scan_id not in _scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")

    del _scan_results[scan_id]
    return {"message": f"Scan {scan_id} deleted"}


@router.post("/scan/upload", response_model=ScanResponse)
async def scan_uploaded_file(
    file: UploadFile = File(...),
    tools: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None
) -> ScanResponse:
    """
    Scan an uploaded HTML file.
    
    Upload a saved HTML file to scan it offline without needing the live website.
    """
    import tempfile
    import json
    from pathlib import Path
    
    # Validate file type
    if not file.filename.endswith(('.html', '.htm')):
        raise HTTPException(
            status_code=400,
            detail="Only HTML files (.html, .htm) are supported"
        )
    
    # Parse tools
    tools_list = json.loads(tools) if tools else None
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.html', delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    scan_id = str(uuid4())
    
    # Create file:// URL
    file_url = Path(tmp_path).absolute().as_uri()
    
    result = ScanResult(
        scan_id=scan_id,
        url=file_url,
        status=ScanStatus.PENDING
    )
    _scan_results[scan_id] = result
    
    # Run scan in background
    async def _scan_file():
        try:
            _scan_results[scan_id].status = ScanStatus.RUNNING
            
            aggregator = ResultsAggregator(tools=tools_list)
            scan_result = await aggregator.scan(file_url)
            scan_result.scan_id = scan_id
            scan_result.url = f"Uploaded file: {file.filename}"
            
            _scan_results[scan_id] = scan_result
            
            # Clean up temp file
            import os
            try:
                os.unlink(tmp_path)
            except:
                pass
                
        except Exception as e:
            logger.error(f"File scan {scan_id} failed: {e}")
            _scan_results[scan_id].status = ScanStatus.FAILED
            _scan_results[scan_id].error = str(e)
    
    # Schedule background task
    import asyncio
    asyncio.create_task(_scan_file())
    
    return ScanResponse(
        scan_id=scan_id,
        status="pending",
        message=f"Scanning uploaded file: {file.filename}"
    )
