"""
Database configuration and connection management
"""
import logging
from typing import AsyncGenerator
from sqlalchemy import create_engine, event, text
from importlib import util as _import_util
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


# Synchronous engine for migrations and initial setup.
# If psycopg2 isn't available (Python 3.13 wheels), automatically fall back to psycopg driver
_sync_db_url = settings.database_url
if _sync_db_url.startswith("postgresql://") and _import_util.find_spec("psycopg2") is None and _import_util.find_spec("psycopg") is not None:
    # Switch to psycopg (psycopg3) dialect
    _sync_db_url = _sync_db_url.replace("postgresql://", "postgresql+psycopg://")

sync_engine = create_engine(
    _sync_db_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,  # Set to True for SQL query logging in development
)

# Asynchronous engine for application use
async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
async_engine = create_async_engine(
    async_database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,  # Set to True for SQL query logging in development
)

# Session makers
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# Connection event handlers for better connection management
# Note: PostgreSQL timezone is already set to UTC by default in most configurations


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get async database session
    
    Yields:
        AsyncSession: Database session for async operations
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session():
    """
    Dependency function to get sync database session
    
    Yields:
        Session: Database session for sync operations
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def init_database():
    """
    Initialize database connection and create tables
    
    This function should be called during application startup
    """
    try:
        # Test async connection
        async with async_engine.begin() as conn:
            logger.info("Successfully connected to database (async)")
            
        # Test sync connection
        with sync_engine.begin() as conn:
            logger.info("Successfully connected to database (sync)")
            
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_database():
    """
    Close database connections
    
    This function should be called during application shutdown
    """
    try:
        await async_engine.dispose()
        sync_engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise


async def check_database_health() -> bool:
    """
    Check database connection health
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False