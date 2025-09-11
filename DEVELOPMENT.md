# Development Setup Guide - AI Closet 2.0

This guide will help you set up the AI Closet 2.0 development environment on a new machine.

## Prerequisites

- **Python 3.13+** (recommended for best compatibility)
- **Node.js 18+** and npm
- **PostgreSQL 14+**
- **Redis 6+**
- **Git**
- **Docker** (optional, for containerized development)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-closet2.0
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env file with your local configuration
# (see Environment Configuration section below)
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb ai_closet

# Run migrations
alembic upgrade head

# Optional: Seed database with test data
python scripts/seed_database.py
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5. Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## Environment Configuration

### Backend (.env file)

Create `backend/.env` with the following configuration:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/ai_closet

# Redis Configuration  
REDIS_URL=redis://localhost:6379

# JWT Configuration
SECRET_KEY=your-secret-key-for-development-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload Configuration
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# Google Cloud Configuration (for AI services)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json

# Fashion-CLIP Service URL (use Cloud Run URL or localhost if running locally)
FASHION_CLIP_SERVICE_URL=https://your-fashion-clip-service-url
# Or for local development:
# FASHION_CLIP_SERVICE_URL=http://localhost:8001

# Development flags
DEBUG=true
TESTING=false
```

### Frontend Environment

Create `frontend/.env.local`:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000

# Development flags
VITE_DEBUG=true
```

## Google Cloud Services Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable the following APIs:
   - Cloud Vision API
   - Vertex AI API
   - Cloud Run API (if using hosted Fashion-CLIP)

### 2. Create Service Account

```bash
# Install Google Cloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Create service account
gcloud iam service-accounts create ai-closet-dev \
    --description="AI Closet Development Service Account" \
    --display-name="AI Closet Dev"

# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:ai-closet-dev@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/vision.imageAnnotator"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:ai-closet-dev@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Download credentials
gcloud iam service-accounts keys create credentials.json \
    --iam-account=ai-closet-dev@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Move credentials to backend directory
mv credentials.json backend/
```

## Running Services

### Development with all services

```bash
# Terminal 1: PostgreSQL (if not running as service)
pg_ctl -D /usr/local/var/postgres start

# Terminal 2: Redis (if not running as service)  
redis-server

# Terminal 3: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 4: Frontend
cd frontend
npm run dev

# Optional Terminal 5: Fashion-CLIP service locally
cd fashion-clip-service
python server.py
```

### Using Docker Compose (Alternative)

```bash
# Start all services with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_clothing_items.py

# Run tests in watch mode during development
pytest-watch
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage
```

## Development Workflow

### 1. Database Migrations

When making database schema changes:

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration file in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### 2. Adding New Dependencies

#### Backend Dependencies

```bash
cd backend

# Add new package
pip install package_name

# Update requirements.txt
pip freeze > requirements.txt

# Or better, add to pyproject.toml and regenerate
pip-compile pyproject.toml
```

#### Frontend Dependencies

```bash
cd frontend

# Add production dependency
npm install package_name

# Add development dependency
npm install --save-dev package_name
```

### 3. Code Quality Tools

#### Backend (Python)

```bash
cd backend

# Format code with Black
black app/

# Sort imports
isort app/

# Lint with flake8
flake8 app/

# Type checking with mypy
mypy app/
```

#### Frontend (TypeScript)

```bash
cd frontend

# Lint code
npm run lint

# Format code
npm run format

# Type checking
npx tsc --noEmit
```

## Common Development Tasks

### 1. Resetting Database

```bash
cd backend

# Drop and recreate database
dropdb ai_closet
createdb ai_closet

# Run migrations
alembic upgrade head

# Seed with test data
python scripts/seed_database.py
```

### 2. Clearing Redis Cache

```bash
redis-cli FLUSHALL
```

### 3. Viewing API Documentation

With the backend running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Database Administration

```bash
# Connect to PostgreSQL
psql ai_closet

# Or use a GUI tool like pgAdmin, DBeaver, or Postico
```

## Troubleshooting

### Common Issues

1. **Python Version Compatibility**
   ```bash
   # Check Python version
   python --version
   
   # Install Python 3.13 via pyenv (recommended)
   pyenv install 3.13.0
   pyenv local 3.13.0
   ```

2. **PostgreSQL Connection Issues**
   ```bash
   # Check if PostgreSQL is running
   pg_isready
   
   # Start PostgreSQL service
   brew services start postgresql # macOS
   sudo service postgresql start # Linux
   ```

3. **Redis Connection Issues**
   ```bash
   # Check if Redis is running
   redis-cli ping
   
   # Start Redis service
   brew services start redis # macOS
   sudo service redis-server start # Linux
   ```

4. **Node.js Version Issues**
   ```bash
   # Use nvm to manage Node.js versions
   nvm install 18
   nvm use 18
   ```

5. **Fashion-CLIP Service Issues**
   - Ensure sufficient memory (8GB+ recommended)
   - Check Cloud Run service status
   - Verify authentication credentials

### Development Tips

1. **Hot Reloading**: Both frontend and backend support hot reloading during development
2. **API Testing**: Use the built-in Swagger UI at `/docs` for interactive API testing
3. **Database Inspection**: Use the `/health/detailed` endpoint to check database connectivity
4. **Logging**: Set `DEBUG=true` in `.env` for detailed logging
5. **CORS**: The backend is configured for local development CORS by default

## IDE Setup

### VS Code (Recommended)

Install these extensions:
- Python (Microsoft)
- Pylance
- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- Thunder Client (for API testing)
- GitLens
- Prettier
- ESLint

### PyCharm

1. Open the `backend` directory as a Python project
2. Configure Python interpreter to use the virtual environment
3. Enable Django support for better FastAPI integration

## Next Steps

1. **Explore the Codebase**: Start with `backend/app/main.py` and `frontend/src/App.tsx`
2. **Read the Architecture Documentation**: Check `docs/architecture/` for detailed system design
3. **Run the Test Suite**: Ensure everything is working correctly
4. **Make Your First Change**: Try adding a simple feature to get familiar with the workflow

For more detailed information, refer to the main README.md and the documentation in the `docs/` directory.
