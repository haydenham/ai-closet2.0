# Fashion AI Platform

A production-ready fashion recommendation platform that provides personalized outfit suggestions by matching AI-generated recommendations to users' uploaded closet items.

## Project Structure

```
├── backend/                 # FastAPI backend service
│   ├── app/                # Application code
│   │   ├── api/           # API routes
│   │   ├── core/          # Core configuration
│   │   ├── models/        # Database models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic
│   ├── tests/             # Backend tests
│   ├── alembic/           # Database migrations
│   └── requirements.txt   # Python dependencies
├── frontend/               # React frontend application
│   ├── src/               # Source code
│   ├── public/            # Static assets
│   └── package.json       # Node.js dependencies
└── docker-compose.yml     # Development environment
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fashion-ai-platform
   ```

2. **Start development services**
   ```bash
   docker-compose up -d postgres redis
   ```

3. **Backend Setup**
   ```bash
   cd backend
   cp .env.example .env
   pip install -r requirements.txt
   make dev
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Testing

**Backend Tests**
```bash
cd backend
make test-cov
```

**Frontend Tests**
```bash
cd frontend
npm run test:coverage
```

### Docker Development

Run the entire stack with Docker:
```bash
docker-compose up
```

## Features

- **User Authentication**: Secure registration, login, and password management
- **Style Profiling**: Personalized AI model assignment through style quiz
- **Closet Management**: Upload and organize clothing items with image processing
- **AI Integration**: Google Cloud AI models for outfit recommendations
- **Outfit Matching**: CLIP embeddings for similarity-based item matching
- **Responsive UI**: Modern React interface with TypeScript

## Technology Stack

**Backend:**
- FastAPI (Python)
- PostgreSQL + SQLAlchemy
- Redis for caching
- JWT authentication
- CLIP for embeddings

**Frontend:**
- React 18 + TypeScript
- React Router + React Query
- Tailwind CSS
- Vite build system

**Infrastructure:**
- Docker containers
- Alembic migrations
- Pytest + Vitest testing

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## Contributing

1. Follow the existing code style and structure
2. Write tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting

## License

[Add your license information here]