"""
FastAPI main application entry point
"""
import logging
from contextlib import asynccontextmanager

# Setup detailed logging first
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from logging_config import setup_detailed_logging
setup_detailed_logging()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Security middleware is optional; gracefully degrade if not present
try:
    from app.middleware.security import SecurityMiddleware  # type: ignore
    _has_security_middleware = True
except Exception:  # broad to avoid test import failures
    _has_security_middleware = False
from app.core.rate_limiting import get_rate_limiter, custom_rate_limit_handler

from app.core.database import init_database, close_database, check_database_health
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.quiz import router as quiz_router
# Temporarily disabled during quiz refactor
# from app.api.feature_learning import router as feature_learning_router
from app.api.closet import router as closet_router
from app.api.outfit_recommendations import router as outfit_recommendations_router
from fastapi.staticfiles import StaticFiles
# Temporarily disabled during quiz refactor
# from app.services.scheduled_learning_service import start_learning_scheduler, stop_learning_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting Fashion AI Platform...")
    try:
        await init_database()
        logger.info("Database initialized successfully")
        
        # TODO: Temporarily disable learning scheduler due to JSON column issues
        # await start_learning_scheduler()
        logger.info("Learning scheduler disabled for development")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Fashion AI Platform...")
    try:
        # TODO: Re-enable when learning scheduler is fixed
        # stop_learning_scheduler()
        logger.info("Learning scheduler was disabled")
        
        await close_database()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


app = FastAPI(
    title="Fashion AI Platform",
    description="Production-ready fashion recommendation platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
limiter = get_rate_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

if _has_security_middleware:
    app.add_middleware(
        SecurityMiddleware,
        enable_rate_limiting=True,
        enable_request_validation=True,
        enable_audit_logging=True
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(quiz_router)
# app.include_router(feature_learning_router)  # Temporarily disabled during quiz refactor
app.include_router(closet_router)
app.include_router(outfit_recommendations_router)

# Mount static files for quiz images
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return {"message": "Fashion AI Platform API"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint that includes database connectivity
    """
    db_healthy = await check_database_health()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected"
    }