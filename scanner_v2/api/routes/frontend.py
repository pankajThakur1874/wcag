"""Frontend serving routes."""

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter(tags=["Frontend"])

# Get the templates directory path
TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "templates"
DASHBOARD_V2_HTML = TEMPLATES_DIR / "dashboard_v2.html"


@router.get("/")
async def serve_root():
    """
    Redirect root to V2 dashboard.

    Returns:
        Redirect to /v2
    """
    return RedirectResponse(url="/v2")


@router.get("/v2")
async def serve_dashboard_v2():
    """
    Serve the V2 dashboard HTML.

    Returns:
        HTML dashboard page
    """
    return FileResponse(DASHBOARD_V2_HTML)


@router.get("/dashboard")
async def serve_dashboard_alt():
    """
    Alternative route to serve the V2 dashboard.

    Returns:
        HTML dashboard page
    """
    return FileResponse(DASHBOARD_V2_HTML)
