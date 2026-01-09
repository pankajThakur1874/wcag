"""FastAPI application for WCAG Scanner."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from src.api.routes import router
from src.utils.config import get_config

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

# Include routes
app.include_router(router)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to docs."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }
