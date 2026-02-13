# WCAG Accessibility Scanner

A comprehensive WCAG (Web Content Accessibility Guidelines) compliance scanner with a modern React frontend and FastAPI backend. Scan websites for accessibility issues, track violations, and generate detailed reports.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Running the Project](#running-the-project)
- [API Documentation](#api-documentation)
- [Environment Configuration](#environment-configuration)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Deployment](#deployment)

---

## ✨ Features

### Backend (FastAPI + Python)
- 🔐 **JWT Authentication** - Secure login with access & refresh tokens
- 📊 **Dashboard Analytics** - Real-time statistics and insights
- 🔍 **Multi-Scanner Support** - Axe, Pa11y, Lighthouse, HTML Validator, and custom scanners
- ⚡ **Async Job Processing** - Background workers with progress tracking
- 📄 **Multiple Report Formats** - HTML, JSON, and CSV exports
- 🗄️ **MongoDB Integration** - Scalable data persistence
- 🎯 **WCAG Compliance Checking** - Comprehensive accessibility testing
- 🔄 **Site-wide Scanning** - Crawl and analyze entire websites

### Frontend (Next.js + React)
- ⚛️ **Modern React 19** - Latest React features
- 🎨 **Tailwind CSS v4** - Beautiful, responsive UI
- 📱 **Responsive Design** - Works on all devices
- 🔒 **Protected Routes** - Secure authentication flow
- 📊 **Interactive Dashboards** - Visualize accessibility data
- 🚀 **Fast & Optimized** - Built with Next.js 16

---

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI 0.109+
- **Language**: Python 3.9+
- **Database**: MongoDB 4.4+
- **Auth**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Browser Automation**: Playwright
- **Async Runtime**: uvicorn with uvloop

### Frontend
- **Framework**: Next.js 16.1
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS v4
- **HTTP Client**: Axios
- **Icons**: Lucide React

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### Required
- **Python 3.9 or higher** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+ and npm** - [Download Node.js](https://nodejs.org/)
- **MongoDB 4.4+** - [Download MongoDB](https://www.mongodb.com/try/download/community)
- **Git** - [Download Git](https://git-scm.com/downloads)

### Optional (Recommended)
- **MongoDB Compass** - GUI for MongoDB
- **Postman** - API testing
- **VS Code** or **IntelliJ IDEA** - Code editors

---

## 📁 Project Structure

```
wcagReport/
├── wcag_backend/          # FastAPI backend
│   ├── api/               # API routes & app
│   ├── core/              # Core business logic
│   ├── database/          # MongoDB models & repositories
│   ├── scanners/          # Accessibility scanners
│   ├── schemas/           # Pydantic schemas
│   ├── workers/           # Background job workers
│   ├── utils/             # Utilities & helpers
│   ├── main.py            # Application entry point
│   ├── config.yaml        # Configuration
│   └── requirements.txt   # Python dependencies
│
├── wcag-frontend/         # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js app directory
│   │   ├── components/    # React components
│   │   └── lib/           # Utilities
│   ├── public/            # Static assets
│   └── package.json       # Node dependencies
│
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/pankajThakur1874/wcag.git
cd wcagReport
```

### 2. Start MongoDB

```bash
# Using Homebrew (macOS)
brew services start mongodb-community

# Or using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Verify MongoDB is running
mongosh --eval "db.version()"
```

### 3. Setup Backend

```bash
cd wcag_backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate    # On Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Create .env file
cp .env.example .env

# Start backend server
python -m wcag_backend.main
```

Backend will be running at **http://localhost:8000**

### 4. Setup Frontend

```bash
# In a new terminal
cd wcag-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be running at **http://localhost:3000**

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

---

## 🔧 Detailed Setup

### Backend Setup

#### 1. Create Virtual Environment

```bash
cd wcag_backend
python3 -m venv .venv
source .venv/bin/activate
```

#### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies include:**
- FastAPI & Uvicorn - Web framework
- Motor & PyMongo - MongoDB async driver
- Pydantic - Data validation
- python-jose - JWT authentication
- passlib & bcrypt - Password hashing
- Playwright - Browser automation
- BeautifulSoup4 & lxml - HTML parsing
- Pillow - Image processing
- And more...

#### 3. Install Playwright Browsers

```bash
playwright install
```

This downloads Chromium, Firefox, and WebKit browsers (~500MB).

#### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017

# Security - CHANGE IN PRODUCTION!
JWT_SECRET=your-super-secret-key-change-this-in-production

# Server Configuration (optional)
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Logging (optional)
LOG_LEVEL=INFO
```

#### 5. Configure Settings (Optional)

Edit `config.yaml` to customize:

```yaml
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
  reload: true

database:
  mongodb_uri: ${MONGODB_URI:-mongodb://localhost:27017}
  database_name: wcag_scanner

security:
  jwt_secret: ${JWT_SECRET}
  jwt_access_expiry: 900      # 15 minutes
  jwt_refresh_expiry: 604800  # 7 days
  cors_origins:
    - http://localhost:3000
    - http://localhost:8000

queue:
  worker_count: 5
  max_queue_size: 1000
  job_timeout: 300

scanning:
  default_scanners:
    - axe
    - html_validator
    - contrast
    - keyboard
    - aria
  max_pages: 50
  max_depth: 3
  timeout: 30
```

---

### Frontend Setup

#### 1. Install Node Dependencies

```bash
cd wcag-frontend
npm install
```

#### 2. Configure API Endpoint (if needed)

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### 3. Build for Production (Optional)

```bash
npm run build
npm start
```

---

## ▶️ Running the Project

### Development Mode

**Terminal 1 - Backend:**
```bash
cd wcag_backend
source .venv/bin/activate
python -m wcag_backend.main
```

**Terminal 2 - Frontend:**
```bash
cd wcag-frontend
npm run dev
```

### Using IntelliJ IDEA

The project includes an IntelliJ run configuration:

1. Open project in IntelliJ IDEA
2. Ensure Python SDK is configured (File → Project Structure → SDKs)
3. Select "WCAG Backend Server" from run configurations dropdown
4. Click the green play button ▶️

---

## 📚 API Documentation

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

#### Authentication (`/api/v2/auth`)
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout and revoke token
- `GET /auth/me` - Get current user info

#### Dashboard (`/api/v2/dashboard`)
- `GET /dashboard/stats` - Get dashboard statistics
- `GET /dashboard/pages` - List all scanned pages

#### Projects (`/api/v2/projects`)
- `GET /projects` - List projects (paginated)
- `POST /projects` - Create project
- `GET /projects/:id` - Get project details
- `PUT /projects/:id` - Update project
- `DELETE /projects/:id` - Delete project

#### Scans (`/api/v2/scans`)
- `POST /scans/quick` - Start quick scan
- `POST /scans/project` - Start project scan
- `GET /scans/:id/status` - Get scan progress
- `GET /scans` - List scans (paginated)
- `GET /scans/:id` - Get scan details

#### Issues (`/api/v2/issues`)
- `GET /scans/:scanId/issues` - List issues for scan
- `PATCH /issues/:issueId` - Update issue status

#### Reports (`/api/v2/reports`)
- `GET /reports` - List reports (completed scans)
- `GET /reports/:id/download?format=html|json|csv` - Download report

---

## ⚙️ Environment Configuration

### Backend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MONGODB_URI` | Yes | `mongodb://localhost:27017` | MongoDB connection string |
| `JWT_SECRET` | Yes | - | Secret key for JWT tokens (use strong random value) |
| `SERVER_HOST` | No | `0.0.0.0` | Server host |
| `SERVER_PORT` | No | `8000` | Server port |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Frontend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend API URL |

---

## 🐛 Troubleshooting

### MongoDB Connection Issues

**Problem**: `Connection refused` or `Cannot connect to MongoDB`

**Solution**:
```bash
# Check if MongoDB is running
ps aux | grep mongod

# Start MongoDB
brew services start mongodb-community  # macOS
sudo systemctl start mongod            # Linux
```

**Test Connection**:
```bash
mongosh mongodb://localhost:27017
```

---

### Backend Won't Start

**Problem**: `ModuleNotFoundError: No module named 'wcag_backend'`

**Solution**:
```bash
# Make sure you're in the project root, not inside wcag_backend
cd /path/to/wcagReport
source wcag_backend/.venv/bin/activate
python -m wcag_backend.main
```

---

### Port Already in Use

**Problem**: `Address already in use: 8000`

**Solution**:
```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
kill -9 $(lsof -ti:8000)

# Or change port in config.yaml
```

---

### Playwright Browser Issues

**Problem**: `Executable doesn't exist` or browser errors

**Solution**:
```bash
# Reinstall Playwright browsers
source .venv/bin/activate
playwright install

# Or install specific browser
playwright install chromium
```

---

### bcrypt / Password Hashing Errors

**Problem**: `password cannot be longer than 72 bytes`

**Solution**: Already fixed in the code. The security module pre-hashes long passwords with SHA256 before bcrypt.

If you still see this error, ensure you have the correct bcrypt version:
```bash
pip install "bcrypt>=4.0.0,<4.2.0" --force-reinstall
```

---

### Frontend Can't Connect to Backend

**Problem**: CORS errors or connection refused

**Solution**:

1. **Check backend is running**: http://localhost:8000/docs
2. **Verify CORS settings** in `config.yaml`:
   ```yaml
   security:
     cors_origins:
       - http://localhost:3000
   ```
3. **Check API URL** in frontend `.env.local`
4. **Restart both servers**

---

## 💻 Development

### Running Tests

**Backend:**
```bash
cd wcag_backend
source .venv/bin/activate
pytest tests/
```

**Frontend:**
```bash
cd wcag-frontend
npm test
```

### Code Style

**Backend** - Follow PEP 8:
```bash
# Format code
black wcag_backend/

# Lint
flake8 wcag_backend/
```

**Frontend** - ESLint:
```bash
npm run lint
```

### Hot Reload

Both backend and frontend support hot reload:
- **Backend**: Auto-reloads on file changes (`reload: true` in config)
- **Frontend**: Next.js Fast Refresh

---

## 🚀 Deployment

### Docker Deployment (Coming Soon)

```bash
# Build and run with docker-compose
docker-compose up -d
```

### Production Checklist

- [ ] Change `JWT_SECRET` to a strong random value
- [ ] Set `MONGODB_URI` to production database
- [ ] Configure CORS for your production domain
- [ ] Enable MongoDB authentication
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure rate limiting
- [ ] Set `reload: false` in backend config
- [ ] Build frontend: `npm run build`
- [ ] Use environment-specific configs
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy for MongoDB

---

## 📝 License

MIT License - see LICENSE file for details

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Support

For issues and questions:
- **GitHub Issues**: [Create an issue](https://github.com/pankajThakur1874/wcag/issues)
- **Documentation**: http://localhost:8000/docs (when running)

---

## 🎯 Roadmap

- [ ] Docker & Docker Compose support
- [ ] CI/CD pipelines
- [ ] Advanced reporting features
- [ ] Scheduled scans
- [ ] Email notifications
- [ ] Multi-tenancy support
- [ ] Advanced analytics dashboard
- [ ] PDF report generation
- [ ] Integration with CI/CD tools
- [ ] Browser extension

---

## 👥 Authors

- **Pankaj Thakur** - Initial work

---

## 🙏 Acknowledgments

- WCAG Guidelines by W3C
- Axe-core accessibility engine
- Pa11y accessibility testing tool
- FastAPI framework
- Next.js framework
- MongoDB database
- All open-source contributors

---

**Made with ❤️ for a more accessible web**
