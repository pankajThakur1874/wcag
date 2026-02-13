# WCAG Backend API v2

Production-ready WCAG accessibility scanner backend with JWT authentication, async job processing, and multi-format reporting.

## Features

✅ **Authentication & Security**
- JWT with access token (15 min) + refresh token (7 days)
- Token rotation for enhanced security
- Bcrypt password hashing
- Role-based access control

✅ **Core Functionality**
- User and project management
- Async scan processing with background workers
- Multi-page site scanning with progress tracking
- Issue tracking and status management
- Dashboard statistics and analytics

✅ **Reporting**
- HTML reports with beautiful styling
- JSON export for integration
- CSV export for spreadsheets
- Downloadable reports

✅ **Scalability**
- MongoDB for persistence
- Background job queue
- Worker pool for concurrent scans
- Horizontal scaling ready

## Quick Start

### Prerequisites

- Python 3.9+
- MongoDB 4.4+
- Node.js (for Playwright browsers)

### Installation

1. **Install dependencies:**
```bash
cd wcag-backend
pip install -r requirements.txt
```

2. **Install Playwright browsers:**
```bash
playwright install
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Start MongoDB:**
```bash
# Using Docker
docker run -d -p 27017:27017 mongo:latest

# Or use your existing MongoDB instance
```

5. **Run the server:**
```bash
python -m wcag_backend.main
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## API Endpoints

### Authentication (`/api/v2/auth`)
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout and revoke token
- `GET /auth/me` - Get current user info

### Dashboard (`/api/v2/dashboard`)
- `GET /dashboard/stats` - Get dashboard statistics
- `GET /dashboard/pages` - List all scanned pages

### Projects (`/api/v2/projects`)
- `GET /projects` - List projects (paginated)
- `POST /projects` - Create project
- `GET /projects/:id` - Get project details
- `PUT /projects/:id` - Update project
- `DELETE /projects/:id` - Delete project

### Scans (`/api/v2/scans`)
- `POST /scans/quick` - Start quick scan
- `POST /scans/project` - Start project scan
- `GET /scans/:id/status` - Get scan progress
- `GET /scans` - List scans (paginated)
- `GET /scans/:id` - Get scan details

### Issues (`/api/v2`)
- `GET /scans/:scanId/issues` - List issues for scan
- `PATCH /issues/:issueId` - Update issue status

### Reports (`/api/v2/reports`)
- `GET /reports` - List reports (completed scans)
- `GET /reports/:id/download?format=html|json|csv` - Download report

## Configuration

Edit `config.yaml` to customize:

```yaml
server:
  host: 0.0.0.0
  port: 8000
  workers: 4

database:
  mongodb_uri: mongodb://localhost:27017
  database_name: wcag_scanner

security:
  jwt_secret: ${JWT_SECRET}
  jwt_access_expiry: 900      # 15 minutes
  jwt_refresh_expiry: 604800  # 7 days

queue:
  worker_count: 5
  max_queue_size: 1000
  job_timeout: 300
```

## Environment Variables

Create a `.env` file:

```bash
# Required
MONGODB_URI=mongodb://localhost:27017
JWT_SECRET=your-secure-random-secret-here

# Optional (defaults in config.yaml)
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=INFO
```

## Architecture

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │ HTTP/REST
       ↓
┌─────────────────────────┐
│   FastAPI API v2        │
│  - Authentication       │
│  - Request Validation   │
│  - Response Formatting  │
└──────┬──────────────────┘
       │
       ├─→ MongoDB (persistence)
       │
       └─→ Queue Manager
              ↓
       ┌────────────────┐
       │  Worker Pool   │
       │  - 5 Workers   │
       │  - Async Jobs  │
       └────────┬───────┘
                │
         ┌──────┴──────┐
         │  Scanner    │
         │  Adapter    │
         └──────┬──────┘
                │
         ┌──────┴──────────┐
         │  src/scanners   │
         │  - Axe          │
         │  - Pa11y        │
         │  - Custom...    │
         └─────────────────┘
```

## Database Schema

### Collections

1. **users** - User accounts
2. **refresh_tokens** - JWT refresh tokens (with TTL)
3. **projects** - Website projects
4. **scans** - Scan jobs and results
5. **issues** - Accessibility issues found

### Indexes

Automatic index creation on startup for optimal query performance.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

```
wcag-backend/
├── api/
│   ├── app.py              # FastAPI app with lifespan
│   ├── dependencies.py     # Dependency injection
│   ├── middleware.py       # Error handling, CORS
│   └── routes/             # API endpoints
├── core/
│   ├── auth_service.py     # JWT authentication
│   ├── scanner_adapter.py  # Scanner integration
│   └── report_generator.py # Report generation
├── database/
│   ├── connection.py       # MongoDB connection
│   ├── models.py           # Pydantic models
│   └── repositories/       # Data access layer
├── schemas/                # Request/response schemas
├── workers/                # Background job processing
│   ├── queue_manager.py
│   ├── worker_pool.py
│   └── scan_worker.py
└── utils/                  # Utilities
    ├── config.py
    ├── logger.py
    ├── exceptions.py
    └── security.py
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y chromium && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY wcag-backend/ wcag-backend/
COPY src/ src/

# Run
CMD ["python", "-m", "wcag_backend.main"]
```

### Security Checklist

- [ ] Change `JWT_SECRET` to a strong random value
- [ ] Use HTTPS in production
- [ ] Configure CORS for your frontend domain
- [ ] Use MongoDB authentication
- [ ] Set up rate limiting
- [ ] Enable MongoDB replica sets for HA
- [ ] Use environment-specific configs

## Troubleshooting

### MongoDB Connection Issues

```bash
# Check MongoDB is running
docker ps | grep mongo

# Test connection
mongosh mongodb://localhost:27017
```

### Worker Not Processing Jobs

Check logs for worker startup:
```bash
# Logs will show:
# Worker pool started with 5 workers
# Worker worker-1 started
```

### Scan Timeouts

Increase timeout in `config.yaml`:
```yaml
queue:
  job_timeout: 600  # 10 minutes
```

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [your-repo/issues]
- Documentation: http://localhost:8000/docs
