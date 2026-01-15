# WCAG Scanner V2

Production-ready WCAG compliance scanner with FastAPI backend, MongoDB storage, and CLI/TUI interface.

## Phase 1 Complete: Foundation Setup ✅
## Phase 2 Complete: Core Scanning Engine ✅
## Phase 3 Complete: Queue System & Workers ✅
## Phase 4 Complete: Database Layer ✅
## Phase 5 Complete: FastAPI Application ✅
## Phase 6 Complete: CLI Commands ✅
## Phase 7 Complete: TUI Dashboard ✅
## Phase 8 Complete: Report Generation ✅

The core infrastructure, scanning engine, worker system, database repositories, REST API, CLI, interactive TUI dashboard, and comprehensive report generation have been implemented:

### Created Files

#### Configuration & Setup
- `requirements.txt` - All dependencies (FastAPI, MongoDB, CLI tools, etc.)
- `config.yaml` - YAML configuration file with environment variable support
- `.env.example.v2` - Example environment variables

#### Utilities (`utils/`)
- `config.py` - Configuration management with Pydantic
- `logger.py` - Structured logging (JSON/standard formats)
- `exceptions.py` - Custom exception classes
- `helpers.py` - Utility functions (URL handling, hashing, serialization)

#### Database (`database/`)
- `connection.py` - MongoDB connection with Motor (async driver)
- `models.py` - Pydantic models for all MongoDB documents

#### Core Scanning Engine (`core/`) ✅
- `crawler.py` - Website crawler with sitemap support
- `wcag_reference.py` - WCAG 2.2 criteria data (86 criteria)
- `page_scanner.py` - Individual page scanning
- `issue_aggregator.py` - Issue deduplication and aggregation
- `compliance_scorer.py` - Weighted compliance scoring
- `scanner_orchestrator.py` - Workflow coordination

#### Services (`services/`) ✅
- `scanner_service.py` - Scanner wrapper (axe-core integration)
- `screenshot_service.py` - Screenshot capture

#### Queue System & Workers (`workers/`, `schemas/`) ✅
- `queue_manager.py` - In-memory async queue with priority
- `scan_worker.py` - Job processing worker
- `worker_pool.py` - Worker lifecycle management
- `schemas/scan.py` - Job and request schemas

#### Database Layer (`database/repositories/`, `schemas/`) ✅
- `repositories/user_repo.py` - User CRUD and authentication
- `repositories/project_repo.py` - Project management and search
- `repositories/scan_repo.py` - Scan lifecycle and statistics
- `repositories/page_repo.py` - Scanned page storage
- `repositories/issue_repo.py` - Issue tracking and filtering
- `schemas/user.py` - User API schemas (create, login, response)
- `schemas/project.py` - Project API schemas (CRUD, list)
- `schemas/issue.py` - Issue API schemas (filtering, updates)

#### FastAPI Application (`api/`) ✅
- `app.py` - FastAPI application with lifespan management
- `dependencies.py` - Dependency injection (DB, repos, auth)
- `middleware.py` - CORS, logging, error handling middleware
- `routes/health.py` - Health check endpoints
- `routes/auth.py` - Authentication (register, login, logout)
- `routes/projects.py` - Project CRUD endpoints
- `routes/scans.py` - Scan management endpoints
- `routes/issues.py` - Issue tracking endpoints
- `routes/reports.py` - Report generation endpoints
- `main_v2.py` (project root) - API server entry point

#### CLI Commands (`cli/`) ✅
- `main.py` - Click CLI application
- `utils.py` - API client and formatting utilities
- `commands/server.py` - Server management (start, stop, status)
- `commands/auth.py` - Authentication commands (register, login, logout, whoami)
- `commands/project.py` - Project commands (list, create, show, update, delete)
- `commands/scan.py` - Scan commands (list, start, show, status, cancel, delete)
- `commands/report.py` - Report commands (view, export, issues)
- `commands/dashboard.py` - TUI dashboard command
- `cli_v2.py` (project root) - CLI entry point

#### TUI Dashboard (`cli/tui/`) ✅
- `app.py` - Textual TUI application with real-time updates
- Auto-refresh every 5 seconds
- Multi-panel layout (stats, scans, projects)
- Keyboard navigation and shortcuts
- `test_phase7_guide.md` (project root) - Phase 7 testing guide

#### Report Templates (`report_templates/`) ✅
- `html_report.jinja2` - Professional HTML report template
- `styles.css` - Comprehensive CSS styling for HTML reports
- `test_phase8_guide.md` (project root) - Phase 8 testing guide

### Directory Structure

```
scanner_v2/
├── api/                    # FastAPI application (Phase 5)
│   ├── routes/
│   └── ...
├── core/                   # Core scanning logic (Phase 2)
├── services/              # External integrations (Phase 2)
├── workers/               # Background workers (Phase 3)
├── database/              # MongoDB operations ✅
│   ├── connection.py      # MongoDB connection ✅
│   ├── models.py          # Document models ✅
│   └── repositories/      # Data access layer ✅
│       ├── user_repo.py   # User repository ✅
│       ├── project_repo.py # Project repository ✅
│       ├── scan_repo.py   # Scan repository ✅
│       ├── page_repo.py   # Page repository ✅
│       └── issue_repo.py  # Issue repository ✅
├── schemas/               # Pydantic API schemas ✅
│   ├── scan.py           # Job schemas ✅
│   ├── user.py           # User schemas ✅
│   ├── project.py        # Project schemas ✅
│   └── issue.py          # Issue schemas ✅
├── cli/                   # CLI interface (Phase 6-7)
│   ├── commands/
│   └── tui/
├── utils/                 # Utilities ✅
│   ├── config.py          # Configuration ✅
│   ├── logger.py          # Logging ✅
│   ├── exceptions.py      # Exceptions ✅
│   └── helpers.py         # Helpers ✅
├── report_templates/      # Report templates (Phase 8)
├── config.yaml           # Configuration ✅
├── requirements.txt      # Dependencies ✅
└── README.md            # This file ✅
```

## MongoDB Collections

The following collections are defined in `models.py`:

- **users** - User accounts
- **projects** - Website projects
- **scans** - Scan executions with progress tracking
- **scanned_pages** - Individual page scan results
- **issues** - Detected accessibility issues
- **wcag_criteria** - WCAG reference data (to be seeded)

## Getting Started

### 1. Install Dependencies

```bash
cd scanner_v2
pip install -r requirements.txt
```

### 2. Setup MongoDB

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:7

# Or install MongoDB locally
```

### 3. Configure Environment

```bash
# Copy example env file
cp ../.env.example.v2 ../.env

# Edit .env with your settings
# Minimal required:
# MONGODB_URI=mongodb://localhost:27017
# JWT_SECRET=your-secret-key
```

### 4. Test Configuration

```python
# Test configuration loading
from scanner_v2.utils.config import load_config

config = load_config()
print(f"Database: {config.database.mongodb_uri}")
print(f"Server: {config.server.host}:{config.server.port}")
```

### 5. Test Database Connection

```python
# Test MongoDB connection
import asyncio
from scanner_v2.database.connection import init_db, close_db
from scanner_v2.utils.config import get_config

async def test_db():
    config = get_config()
    db = await init_db(config)
    print("Connected to MongoDB!")
    await close_db()

asyncio.run(test_db())
```

## Configuration

Configuration is loaded from `config.yaml` with environment variable substitution:

```yaml
database:
  mongodb_uri: ${MONGODB_URI:-mongodb://localhost:27017}
  database_name: wcag_scanner

scanning:
  default_max_depth: 3
  default_max_pages: 100
  default_wcag_level: "AA"
```

Environment variables use the format: `${VAR_NAME:-default_value}`

## Logging

Two logging formats supported:

**Standard** (human-readable):
```python
from scanner_v2.utils.logger import setup_logging

logger = setup_logging(level="INFO", format_type="standard")
logger.info("Starting scan...")
```

**JSON** (structured):
```python
logger = setup_logging(level="INFO", format_type="json")
logger.info("Starting scan...", extra={"scan_id": "123", "duration_ms": 1500})
```

## Exception Handling

Custom exceptions for different error types:

```python
from scanner_v2.utils.exceptions import (
    ScanNotFoundException,
    DatabaseConnectionError,
    InvalidURLError
)

try:
    # ... scan logic
    raise ScanNotFoundException(scan_id="123")
except ScanNotFoundException as e:
    print(f"Error: {e.message}")
    print(f"Details: {e.details}")
```

## Models

All MongoDB documents use Pydantic models for validation:

```python
from scanner_v2.database.models import (
    Project, ProjectSettings,
    Scan, ScanConfig, ScanStatus,
    Issue, ImpactLevel
)

# Create a project
project = Project(
    user_id="user123",
    name="My Website",
    base_url="https://example.com",
    settings=ProjectSettings(
        max_depth=3,
        max_pages=100,
        wcag_level="AA"
    )
)

# Access enums
status = ScanStatus.COMPLETED
impact = ImpactLevel.CRITICAL
```

## Phase 2 Features

### Website Crawler
- Async crawling with Playwright
- Sitemap.xml support for faster discovery
- Configurable depth and page limits
- Robots.txt respect
- URL filtering (include/exclude patterns)
- Same-domain enforcement

### WCAG 2.2 Reference
- All 86 success criteria
- Automation level classification
- 29-35% fully automated
- 40-47% partially automated
- 18-29% manual only

### Scanner Service
- axe-core integration (working)
- pa11y integration (placeholder)
- Lighthouse integration (placeholder)
- Unified scanner interface
- Parallel scanner execution
- Result normalization

### Issue Processing
- Issue deduplication by signature
- Multi-scanner aggregation
- Impact level determination
- WCAG criteria mapping
- Instance tracking

### Compliance Scoring
- Weighted scoring algorithm
- Impact-based weighting (critical=10, serious=5, moderate=2, minor=1)
- WCAG level weighting (A=3, AA=2, AAA=1)
- Principle-based scoring
- Compliance level determination

### Scanner Orchestrator
- Complete workflow coordination
- Progress tracking
- Error handling
- Callback support for real-time updates

## Phase 3 Features

### Queue Manager
- In-memory asyncio.Queue implementation
- Separate queues for orchestration and page scans
- Priority-based job scheduling (1-10 scale)
- Job status tracking (pending, running, completed, failed, cancelled)
- Automatic job retry with exponential backoff
- Configurable max retries per job
- Job callbacks for completion notifications
- Automatic cleanup of old completed jobs
- Queue statistics and monitoring

### Scan Worker
- Async job processing from queue
- Configurable job timeout
- Support for multiple job types:
  - Scan orchestration (full website scans)
  - Page scans (individual page scanning)
- Error handling with retry logic
- Worker status reporting
- Graceful shutdown

### Worker Pool
- Dynamic worker management
- Configurable worker count (default: 5)
- Worker lifecycle management (start/stop)
- Dynamic scaling (add/remove workers at runtime)
- Health monitoring
- Automatic cleanup background task
- Pool status and statistics
- Graceful shutdown of all workers

### Job System
- Pydantic schemas for type safety
- Job priority levels (low, normal, high, urgent)
- Retry mechanism with exponential backoff
- Job tracking and history
- Concurrent job processing
- Worker assignment tracking

## Testing Phase 3

```bash
# Run Phase 3 tests
python test_phase3.py
```

Tests:
- Queue manager (enqueue, dequeue, priorities)
- Scan worker (job processing)
- Worker pool (multiple workers)
- Job retry mechanism
- Concurrent worker processing

## Phase 4 Features

### Repository Pattern
- Clean separation of data access logic
- Async operations throughout
- Type-safe with Pydantic models
- Consistent error handling
- Optimized queries with indexes

### User Repository
- User CRUD operations
- Secure password hashing with bcrypt
- Email-based authentication
- Password change functionality
- User lookup by ID or email
- Role-based user management

### Project Repository
- Project lifecycle management
- User-scoped project listing
- Project search by name/URL
- Settings management
- Pagination support
- Soft delete capability

### Scan Repository
- Scan creation and tracking
- Status lifecycle management (queued → scanning → completed/failed/cancelled)
- Progress tracking with real-time updates
- Results aggregation (summary and scores)
- Scan statistics and analytics
- Historical scan queries by status
- Recent scans across all projects
- Automatic timestamp management (started_at, completed_at)

### Page Repository
- Individual page result storage
- Batch page creation for performance
- Scan-scoped page queries with pagination
- URL-based page lookup
- Raw scanner results storage (axe, pa11y, lighthouse)
- Compliance score per page
- Cascade deletion with scan

### Issue Repository
- Issue creation and tracking
- Bulk issue creation for efficiency
- Advanced filtering:
  - By impact level (critical, serious, moderate, minor)
  - By WCAG level (A, AA, AAA)
  - By WCAG principle (perceivable, operable, understandable, robust)
  - By status (open, fixed, false_positive, ignored)
- Issue status updates with notes
- Aggregated issue summaries for scans
- Page-scoped issue queries
- Manual review flagging

### API Schemas
- Request/response validation with Pydantic
- Type-safe user operations (registration, login)
- Project management schemas (create, update, list)
- Issue filtering and update schemas
- Automatic serialization/deserialization
- Email validation for user accounts
- URL validation for projects

## Testing Phase 4

```bash
# Run Phase 4 tests
python test_phase4.py
```

Tests:
- UserRepository - User CRUD and authentication (password hashing, login)
- ProjectRepository - Project management and search
- ScanRepository - Scan lifecycle, status updates, progress tracking, statistics
- PageRepository - Page storage, retrieval, and batch operations
- IssueRepository - Issue tracking, filtering, aggregation, summaries
- All repositories - Data cleanup and cascade deletes

## Example Usage (Phase 4)

```python
import asyncio
from scanner_v2.utils.config import load_config
from scanner_v2.database.connection import MongoDB
from scanner_v2.database.repositories.user_repo import UserRepository
from scanner_v2.database.repositories.project_repo import ProjectRepository
from scanner_v2.database.repositories.scan_repo import ScanRepository
from scanner_v2.database.models import UserRole, ScanType, ScanStatus, ProjectSettings

async def example():
    # Setup
    config = load_config()
    db = MongoDB(config)
    await db.connect()

    # Initialize repositories
    user_repo = UserRepository(db.db)
    project_repo = ProjectRepository(db.db)
    scan_repo = ScanRepository(db.db)

    # Create user
    user = await user_repo.create(
        email="user@example.com",
        password="SecurePass123",
        name="John Doe",
        role=UserRole.USER
    )
    print(f"Created user: {user.id}")

    # Authenticate user
    auth_user = await user_repo.authenticate("user@example.com", "SecurePass123")
    print(f"Authenticated: {auth_user.email}")

    # Create project
    project = await project_repo.create(
        user_id=user.id,
        name="My Website",
        base_url="https://example.com",
        settings=ProjectSettings(max_depth=3, max_pages=100)
    )
    print(f"Created project: {project.id}")

    # Create scan
    scan = await scan_repo.create(
        project_id=project.id,
        scan_type=ScanType.FULL
    )
    print(f"Created scan: {scan.id} - Status: {scan.status.value}")

    # Update scan status to scanning
    await scan_repo.update_status(scan.id, ScanStatus.SCANNING)
    print("Scan started")

    # Update progress
    from scanner_v2.database.models import ScanProgress
    progress = ScanProgress(
        total_pages=50,
        pages_crawled=25,
        pages_scanned=10,
        current_page="https://example.com/about"
    )
    await scan_repo.update_progress(scan.id, progress)
    print(f"Progress: {progress.pages_scanned}/{progress.total_pages}")

    # Complete scan with results
    from scanner_v2.database.models import ScanSummary, ScanScores
    summary = ScanSummary(
        total_issues=15,
        by_impact={"critical": 2, "serious": 5, "moderate": 6, "minor": 2},
        by_wcag_level={"A": 5, "AA": 8, "AAA": 2}
    )
    scores = ScanScores(
        overall=85.5,
        by_principle={"perceivable": 88.0, "operable": 83.0, "understandable": 86.0, "robust": 85.0}
    )
    await scan_repo.update_results(scan.id, summary, scores)
    await scan_repo.update_status(scan.id, ScanStatus.COMPLETED)
    print(f"Scan completed - Score: {scores.overall}/100")

    # Get all scans for project
    scans, total = await scan_repo.get_by_project(project.id)
    print(f"Project has {total} scans")

    # Get scan statistics
    stats = await scan_repo.get_statistics(project_id=project.id)
    print(f"Scan stats: {stats}")

    # Search projects
    results, count = await project_repo.search(user.id, query="example")
    print(f"Found {count} projects matching 'example'")

    # Cleanup
    await db.disconnect()

asyncio.run(example())
```

## Phase 5 Features

### FastAPI Application
- Production-ready REST API with OpenAPI documentation
- Lifespan management (startup/shutdown hooks)
- Automatic MongoDB and worker pool initialization
- Graceful shutdown handling

### Middleware
- **CORS**: Configurable cross-origin resource sharing
- **Logging**: Request/response logging with duration tracking
- **Error Handling**: Global exception handling with custom error responses
- Custom headers (X-Process-Time for request duration)

### Authentication & Authorization
- JWT token-based authentication
- User registration and login endpoints
- Secure password hashing with bcrypt
- Protected routes with Bearer token validation
- Current user dependency injection
- Token expiry configuration

### API Endpoints

**Health & Status (`/api/v1/health`)**:
- `GET /` - Basic health check
- `GET /status` - Detailed system status (DB, queue, workers)

**Authentication (`/api/v1/auth`)**:
- `POST /register` - User registration
- `POST /login` - User login (returns JWT token)
- `GET /me` - Get current user info
- `POST /logout` - Logout

**Projects (`/api/v1/projects`)**:
- `GET /` - List projects with pagination and search
- `POST /` - Create new project
- `GET /{id}` - Get project details
- `PUT /{id}` - Update project
- `DELETE /{id}` - Delete project

**Scans (`/api/v1/scans`, `/api/v1/projects/{id}/scans`)**:
- `POST /projects/{id}/scans` - Create and enqueue scan
- `GET /scans` - List scans with filters
- `GET /scans/{id}` - Get scan details
- `GET /scans/{id}/status` - Real-time scan status
- `POST /scans/{id}/cancel` - Cancel running scan
- `DELETE /scans/{id}` - Delete scan and related data

**Issues (`/api/v1/issues`)**:
- `GET /` - List issues with advanced filtering
- `GET /{id}` - Get issue details
- `PUT /{id}/status` - Update issue status
- `GET /scans/{id}/summary` - Get issue summary

**Reports (`/api/v1/scans/{id}/reports`)**:
- `GET /json` - Comprehensive JSON report
- `GET /html` - HTML report (Phase 8)
- `GET /csv` - CSV export (Phase 8)

### Dependency Injection
- Database connection injection
- Repository injection (all 5 repositories)
- Queue manager injection
- Current user injection
- Configuration injection

### Request/Response Validation
- Automatic validation with Pydantic models
- Type-safe request parsing
- Email and URL validation
- Enum validation for status fields

### Error Handling
- Custom exception mapping to HTTP status codes
- Structured error responses
- Database error handling
- Validation error details
- Authentication error handling

## Testing Phase 5

```bash
# Start the API server (in one terminal)
python main_v2.py

# Run Phase 5 tests (in another terminal)
python test_phase5.py
```

Tests:
- Health check endpoints
- User registration and authentication
- JWT token generation and validation
- Project CRUD operations
- Project search functionality
- Scan creation and enqueuing
- Scan status tracking
- Scan cancellation
- JSON report generation
- Data cleanup and cascade deletes

## Example Usage (Phase 5)

```bash
# Start the API server
python main_v2.py

# Server runs on http://localhost:8000
# OpenAPI docs available at http://localhost:8000/docs
# ReDoc available at http://localhost:8000/redoc
```

Using the API with curl:

```bash
# Health check
curl http://localhost:8000/api/v1/health/

# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123","name":"John Doe"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123"}'

# Create project (use token from login)
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Website","base_url":"https://example.com","description":"Test project"}'

# Create scan
curl -X POST http://localhost:8000/api/v1/projects/PROJECT_ID/scans \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"scan_type":"full","max_pages":10,"max_depth":2}'

# Get scan status
curl http://localhost:8000/api/v1/scans/SCAN_ID/status \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get JSON report
curl http://localhost:8000/api/v1/scans/SCAN_ID/reports/json \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

Using the API with Python (httpx):

```python
import asyncio
import httpx

async def example():
    async with httpx.AsyncClient() as client:
        # Register
        response = await client.post(
            "http://localhost:8000/api/v1/auth/register",
            json={"email": "user@example.com", "password": "Pass123", "name": "User"}
        )
        print(f"User registered: {response.status_code}")

        # Login
        response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": "user@example.com", "password": "Pass123"}
        )
        data = response.json()
        token = data["access_token"]
        print(f"Token: {token[:20]}...")

        # Create project
        response = await client.post(
            "http://localhost:8000/api/v1/projects/",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "My Site", "base_url": "https://example.com"}
        )
        project = response.json()
        print(f"Project created: {project['id']}")

        # Create scan
        response = await client.post(
            f"http://localhost:8000/api/v1/projects/{project['id']}/scans",
            headers={"Authorization": f"Bearer {token}"},
            json={"max_pages": 5, "max_depth": 1}
        )
        scan = response.json()
        print(f"Scan created: {scan['id']}, Status: {scan['status']}")

asyncio.run(example())
```

## Phase 6 Features

### CLI Commands with Click
- Production-ready command-line interface
- Nested command groups (server, auth, project, scan, report)
- Rich terminal output with colors and formatting
- Progress bars for long-running operations
- Configuration stored in `~/.wcag-scanner/config.json`

### Server Management
- `wcag-v2 server start` - Start API server in background
- `wcag-v2 server stop` - Stop running server
- `wcag-v2 server status` - Check server status and health
- `wcag-v2 server restart` - Restart server
- PID tracking in `~/.wcag-scanner/server.pid`

### Authentication Commands
- `wcag-v2 auth register` - Register new user
- `wcag-v2 auth login` - Login and save JWT token
- `wcag-v2 auth logout` - Logout and clear token
- `wcag-v2 auth whoami` - Show current user
- Token auto-saved to config file

### Project Management
- `wcag-v2 project list` - List all projects with table view
- `wcag-v2 project create` - Create new project
- `wcag-v2 project show` - Show project details with formatted panel
- `wcag-v2 project update` - Update project properties
- `wcag-v2 project delete` - Delete project (with confirmation)
- Search functionality with `--search` flag

### Scan Management
- `wcag-v2 scan start` - Create and enqueue new scan
- `wcag-v2 scan list` - List scans with status/progress table
- `wcag-v2 scan show` - Show detailed scan information
- `wcag-v2 scan status` - Check real-time scan status
- `wcag-v2 scan cancel` - Cancel running scan
- `wcag-v2 scan delete` - Delete scan and related data
- `--wait` flag to wait for scan completion with progress bar
- `--follow` flag to track scan progress in real-time

### Report Commands
- `wcag-v2 report view` - View formatted text report in terminal
- `wcag-v2 report export` - Export report to file (JSON, HTML, CSV)
- `wcag-v2 report issues` - List issues with filters
- Rich formatted output with colors and tables
- Issue filtering by impact and WCAG level

### Terminal Formatting
- Beautiful tables with Rich library
- Color-coded status indicators
- Formatted panels for detailed views
- Progress bars with spinners
- Error/success/warning/info message formatting

## Testing Phase 6

```bash
# Start API server first
python main_v2.py

# Run Phase 6 tests (in another terminal)
./test_phase6.sh
```

Tests:
- Server management commands
- User authentication flow
- Project CRUD operations
- Scan creation and monitoring
- Scan status tracking with progress
- Report viewing and export
- Issue listing with filters
- Terminal formatting and colors

## Example Usage (Phase 6)

```bash
# Server management
wcag-v2 server start
wcag-v2 server status

# Authentication
wcag-v2 auth register --email user@example.com --password Pass123 --name "User"
wcag-v2 auth login --email user@example.com --password Pass123
wcag-v2 auth whoami

# Project management
wcag-v2 project create "My Website" "https://example.com" --description "Test site"
wcag-v2 project list
wcag-v2 project list --search example
wcag-v2 project show PROJECT_ID

# Scan management
wcag-v2 scan start PROJECT_ID --max-pages 10 --max-depth 2
wcag-v2 scan start PROJECT_ID --wait  # Wait for completion
wcag-v2 scan list
wcag-v2 scan show SCAN_ID
wcag-v2 scan status SCAN_ID
wcag-v2 scan status SCAN_ID --follow  # Follow progress

# Reports
wcag-v2 report view SCAN_ID
wcag-v2 report view SCAN_ID --format json
wcag-v2 report export SCAN_ID --output report.json --format json
wcag-v2 report issues SCAN_ID --impact critical --limit 20

# Cleanup
wcag-v2 scan delete SCAN_ID --yes
wcag-v2 project delete PROJECT_ID --yes
wcag-v2 auth logout
wcag-v2 server stop
```

## Phase 7 Features

### TUI Dashboard with Textual
- Interactive real-time dashboard
- Built with Textual framework
- Responsive terminal UI
- Auto-refresh every 5 seconds

### Multi-Panel Layout
- **Statistics Panel** (top): Shows overview metrics
  - Total projects count
  - Total scans count
  - Total issues found
  - Scan status breakdown (completed, scanning, failed)
- **Scans Table** (left): Recent scans with live updates
  - Scan ID, Project ID, Status
  - Progress (pages scanned/total)
  - Issues count, Compliance score
  - Color-coded status indicators
- **Projects Table** (right): Active projects list
  - Project ID and name
  - Quick reference for available projects

### Keyboard Shortcuts
- **q** - Quit dashboard
- **r** - Refresh data immediately
- **s** - Switch to scans view
- **p** - Switch to projects view
- **d** - Return to dashboard view

### Real-Time Updates
- Auto-refresh every 5 seconds
- Watch scan status changes in real-time
- Progress numbers update automatically
- New scans appear without manual refresh
- Statistics update dynamically

### Interactive Features
- Click buttons with mouse
- Navigate tables with arrow keys
- Row selection in tables
- Zebra striping for better readability
- Notifications for actions

### Visual Styling
- Color-coded status indicators:
  - Green: Completed
  - Yellow: Scanning
  - Red: Failed
  - Blue: Queued
- Bordered panels for clear separation
- Bold statistics for emphasis
- Custom CSS styling with Textual

## Testing Phase 7

See detailed testing guide in `test_phase7_guide.md`

```bash
# Prerequisites
python main_v2.py  # API server must be running
python cli_v2.py auth login  # Must be authenticated

# Launch dashboard
python cli_v2.py dashboard
```

Dashboard controls:
- Press **q** to quit
- Press **r** to force refresh
- Wait 5 seconds for auto-refresh
- Click buttons with mouse

## Example Usage (Phase 7)

```bash
# Launch TUI dashboard
wcag-v2 dashboard

# Or with full workflow
wcag-v2 auth login --email user@example.com --password Pass123
wcag-v2 project create "My Site" "https://example.com"
wcag-v2 scan start PROJECT_ID --max-pages 10
wcag-v2 dashboard  # Watch scan progress in real-time
```

Dashboard will show:
- Real-time scan progress
- Live status updates
- Statistics overview
- All projects and scans

Press 'q' when done viewing.

## Phase 8 Features

### Professional HTML Reports
- **Executive Summary**: Overall compliance score, WCAG principles breakdown, statistics
- **Score Visualization**: Color-coded score circles (green ≥90, blue ≥70, yellow ≥50, red <50)
- **Progress Bars**: Visual representation of principle-level scores
- **Gradient Design**: Professional purple gradient header
- **Responsive Layout**: Works on desktop, tablet, and mobile devices

### HTML Report Sections
1. **Executive Summary**
   - Overall compliance score with color-coded circle
   - WCAG principles scores (Perceivable, Operable, Understandable, Robust)
   - Summary statistics (pages, issues by impact)
   - WCAG level compliance (A, AA, AAA)

2. **Issues by Impact**
   - Interactive filter buttons (All, Critical, Serious, Moderate, Minor)
   - Color-coded impact headings
   - Issue cards with:
     - Impact badges
     - WCAG criteria tags
     - Description and rule ID
     - Help text and documentation links
     - Fix suggestions
     - Expandable instance details (selector, HTML, context)

3. **Issues by WCAG Criteria**
   - Organized by WCAG criterion (e.g., 1.1.1, 1.4.3, 2.1.1)
   - Issue counts per criterion
   - Impact badges for each issue
   - Instance counts

4. **Page-by-Page Analysis**
   - Sortable table with all scanned pages
   - Columns: URL, Title, Issues, Score, Load Time, Status Code
   - Clickable URLs (open in new tab)
   - Color-coded scores and status indicators

5. **WCAG Compliance Checklist**
   - Organized by Level A, AA, AAA
   - Checkmarks (✓) for passed criteria
   - Cross marks (✗) for failed criteria
   - Issue counts for failed items
   - Color-coded (green/red) for quick assessment

### HTML Report Features
- **Inline CSS**: No external dependencies, single-file portability
- **Print Friendly**: Optimized print stylesheet included
- **Accessible**: WCAG compliant (dogfooding!)
- **Interactive**: JavaScript-powered filtering
- **Professional**: Suitable for client delivery
- **Keyboard Accessible**: Ctrl/Cmd+P for printing

### CSV Reports
- **Comprehensive Data Export**: All issue data in spreadsheet format
- **Columns**:
  - Issue ID, Page URL, Page Title
  - Rule ID, Description
  - Impact, WCAG Level, WCAG Criteria
  - Principle, Help Text, Help URL
  - Detected By, Instances Count
  - Status, Manual Review Required, Fix Suggestion
- **Excel Compatible**: Opens correctly in Excel, Google Sheets, Numbers
- **UTF-8 Encoded**: Preserves special characters
- **Proper Escaping**: Handles commas, quotes, newlines correctly

### JSON Reports (Enhanced)
- **Structured Data**: Complete scan data in JSON format
- **Sections**: Scan metadata, project info, summary, scores, pages, issues
- **Machine Readable**: Easy to integrate with other tools
- **API Compatible**: Same structure as API responses

### Report API Endpoints
- `GET /scans/{id}/reports/json` - JSON report with full data
- `GET /scans/{id}/reports/html` - Beautiful HTML report
- `GET /scans/{id}/reports/csv` - Spreadsheet-compatible CSV export

### CLI Report Commands (Enhanced)
```bash
# View report in terminal
wcag-v2 report view SCAN_ID

# Export JSON report
wcag-v2 report export SCAN_ID -o report.json -f json

# Export HTML report
wcag-v2 report export SCAN_ID -o report.html -f html

# Export CSV report
wcag-v2 report export SCAN_ID -o report.csv -f csv

# List issues with filters
wcag-v2 report issues SCAN_ID --impact critical
wcag-v2 report issues SCAN_ID --wcag-level AA
```

## Testing Phase 8

See detailed testing guide in `test_phase8_guide.md`

```bash
# Prerequisites
python main_v2.py  # API server running
python cli_v2.py auth login  # Authenticated
# Create project and run scan
PROJECT_ID=$(wcag-v2 project create "Test" "https://example.com" | grep "ID:" | awk '{print $2}')
SCAN_ID=$(wcag-v2 scan start $PROJECT_ID --max-pages 5 --wait | grep "Scan ID:" | awk '{print $3}')

# Generate reports
wcag-v2 report export $SCAN_ID -o report.html -f html
wcag-v2 report export $SCAN_ID -o report.csv -f csv
wcag-v2 report export $SCAN_ID -o report.json -f json

# Open HTML report
open report.html  # macOS
xdg-open report.html  # Linux
```

## Example Usage (Phase 8)

```bash
# Complete workflow with report generation
wcag-v2 auth login --email user@example.com --password Pass123
wcag-v2 project create "My Website" "https://example.com"
wcag-v2 scan start PROJECT_ID --max-pages 20 --wait

# Generate and view reports
wcag-v2 report view SCAN_ID  # View in terminal
wcag-v2 report export SCAN_ID -o report.html -f html
open report.html  # Open in browser

# Export for different audiences
wcag-v2 report export SCAN_ID -o client_report.html -f html  # For clients
wcag-v2 report export SCAN_ID -o issues.csv -f csv  # For developers
wcag-v2 report export SCAN_ID -o data.json -f json  # For integrations

# Filter issues
wcag-v2 report issues SCAN_ID --impact critical --limit 10
wcag-v2 report issues SCAN_ID --wcag-level AA
```

**HTML Report Features**:
- Beautiful executive summary with scores
- Interactive issue filtering
- Expandable issue details
- Print-ready formatting
- Mobile-responsive design
- Accessibility compliant

**CSV Report Use Cases**:
- Import into Excel for analysis
- Track issues in project management tools
- Create custom reports and dashboards
- Share with development teams

## Example Usage (Phase 3)

```python
import asyncio
from scanner_v2.workers.worker_pool import init_worker_pool, stop_worker_pool
from scanner_v2.workers.queue_manager import get_queue_manager
from scanner_v2.schemas.scan import JobType, JobPriority

async def process_scans():
    # Initialize worker pool with 5 workers
    pool = await init_worker_pool(worker_count=5, job_timeout=300)

    # Get queue manager
    queue_manager = get_queue_manager()

    # Enqueue a scan job
    job_id = await queue_manager.enqueue_job(
        job_type=JobType.SCAN_ORCHESTRATION,
        payload={
            "scan_id": "scan_123",
            "project_id": "project_456",
            "base_url": "https://example.com",
            "config": {
                "max_depth": 2,
                "max_pages": 20,
                "scanners": ["axe"],
                "wcag_level": "AA"
            }
        },
        priority=JobPriority.HIGH.value
    )

    print(f"Enqueued job: {job_id}")

    # Check pool status
    status = pool.get_status()
    print(f"Active workers: {status['active_workers']}")
    print(f"Queue sizes: {status['queue_stats']}")

    # Wait for processing
    await asyncio.sleep(10)

    # Check job status
    job = queue_manager.get_job_status(job_id)
    print(f"Job status: {job.status.value if job else 'not found'}")

    # Stop worker pool gracefully
    await stop_worker_pool()

asyncio.run(process_scans())
```

## Next Steps

All core phases (1-8) are complete! ✅

**Optional Enhancements**:
- **PDF Generation**: Convert HTML reports to PDF
- **Chart Visualizations**: Add interactive charts to HTML reports (Chart.js/D3.js)
- **Trend Analysis**: Compare scores across multiple scans over time
- **Custom Templates**: Allow users to customize report templates
- **Email Delivery**: Schedule and email reports automatically
- **Screenshot Gallery**: Organize and display issue screenshots
- **Issue Tracking Integration**: Export to Jira, GitHub Issues, etc.
- **CI/CD Integration**: GitHub Actions, GitLab CI plugins
- **Docker Compose**: Production deployment stack
- **Performance Optimization**: Caching, CDN support for reports

## Development Notes

- Uses async/await throughout for non-blocking operations
- MongoDB indexes created automatically on connection
- Type-safe configuration with Pydantic
- Structured logging for production debugging
- Reuses existing scanners from `src/scanners/`

## Testing Phase 1

```python
# test_phase1.py
import asyncio
from scanner_v2.utils.config import get_config
from scanner_v2.utils.logger import setup_logging, get_logger
from scanner_v2.database.connection import init_db, close_db
from scanner_v2.database.models import Project, ProjectSettings

async def main():
    # Setup
    config = get_config()
    setup_logging(level="INFO", format_type="standard")
    logger = get_logger("test")

    # Test database
    logger.info("Testing MongoDB connection...")
    db = await init_db(config)

    # Test model
    project = Project(
        user_id="test_user",
        name="Test Project",
        base_url="https://example.com",
        settings=ProjectSettings()
    )

    logger.info(f"Created project: {project.name}")

    await close_db()
    logger.info("Phase 1 test complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

Run with:
```bash
python test_phase1.py
```

## Architecture Decisions

1. **Motor (async MongoDB)**: Non-blocking database operations
2. **Pydantic**: Type-safe models and configuration
3. **Structured Logging**: Production-ready with JSON support
4. **Environment Variables**: Secure configuration management
5. **Enum-based Status**: Type-safe status values

## Testing Phase 2

```bash
# Run Phase 2 tests
python test_phase2.py
```

Tests:
- WCAG reference data (86 criteria)
- Website crawler (sitemap + web crawling)
- Issue aggregator (deduplication)
- Compliance scorer (weighted scoring)
- Scanner orchestrator (initialization)

## Example Usage (Phase 2)

```python
import asyncio
from scanner_v2.core.scanner_orchestrator import scan_orchestrator

async def scan_website():
    # Configure scan
    config = {
        "max_depth": 2,
        "max_pages": 10,
        "scanners": ["axe"],
        "wcag_level": "AA",
        "screenshot_enabled": True,
        "wait_time": 2000,
    }

    # Execute scan
    results = await scan_orchestrator.execute_scan(
        base_url="https://example.com",
        scan_id="scan_123",
        config=config
    )

    print(f"Scanned {results['pages_scanned']} pages")
    print(f"Found {results['summary']['total_issues']} issues")
    print(f"Compliance score: {results['scores']['overall']}/100")

asyncio.run(scan_website())
```

---

**Status**: Phase 6 Complete ✅
**Next**: Phase 7 - TUI Dashboard

## What Works Now (Phases 1-6)

You can now:
- ✅ Configure the system with YAML and environment variables
- ✅ Connect to MongoDB (async with Motor)
- ✅ Crawl websites to discover pages
- ✅ Scan pages with axe-core for accessibility issues
- ✅ Capture screenshots of issues
- ✅ Deduplicate and aggregate issues
- ✅ Calculate WCAG compliance scores
- ✅ Enqueue scan jobs with priorities
- ✅ Process jobs concurrently with worker pool
- ✅ Retry failed jobs automatically
- ✅ Monitor queue and worker health
- ✅ Scale workers dynamically
- ✅ Create and authenticate users with secure password hashing
- ✅ Manage projects with full CRUD operations
- ✅ Track scan lifecycle from queued to completed
- ✅ Store and retrieve scanned pages with results
- ✅ Filter and query issues by multiple criteria
- ✅ Generate scan statistics and summaries
- ✅ Persist all scan data to MongoDB
- ✅ Access REST API with JWT authentication
- ✅ Use OpenAPI documentation at /docs
- ✅ Create and manage scans via HTTP endpoints
- ✅ Get real-time scan status via API
- ✅ Generate JSON reports via API
- ✅ Global error handling and logging
- ✅ Use CLI commands to manage server, projects, and scans
- ✅ Start/stop API server from CLI
- ✅ Beautiful terminal output with Rich formatting
- ✅ Progress bars for scan monitoring
- ✅ Export reports to JSON format
- ✅ Filter and view issues from terminal

**Ready for**: Phase 7 will add an interactive TUI dashboard for real-time monitoring!
