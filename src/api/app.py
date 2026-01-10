"""FastAPI application for WCAG Scanner."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.utils.config import get_config, get_templates_dir

config = get_config()

app = FastAPI(
    title="WCAG Accessibility Scanner API",
    description="""
    A comprehensive API for scanning websites for WCAG 2.2 accessibility violations.

    ## Features
    - Multiple scanning tools (axe-core, Pa11y, Lighthouse, etc.)
    - WCAG 2.2 compliance checking
    - Detailed violation reports
    - HTML and JSON report formats

    ## Quick Start
    1. POST `/api/v1/scan` with a URL to start scanning
    2. GET `/api/v1/scan/{scan_id}` to check status and get results
    3. GET `/api/v1/scan/{scan_id}/report` for formatted reports
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/", include_in_schema=False, response_class=HTMLResponse)
async def root():
    """Serve the web UI."""
    template_path = get_templates_dir() / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text())
    return HTMLResponse(content="<h1>WCAG Scanner</h1><p>UI not found. Visit <a href='/docs'>/docs</a> for API.</p>")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }
