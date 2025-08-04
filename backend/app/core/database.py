"""
Database configuration and connection management
"""
import logging
from typing import AsyncGenerator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


# Synchronous engine for migrations and initial setup
sync_engine = create_engine(
    settings.database_url,
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
    poolclass=QueuePool,
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
@event.listens_for(sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set database connection parameters for better performance"""
    if "postgresql" in settings.database_url:
        # PostgreSQL specific settings
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET timezone TO 'UTC'")


@event.listens_for(async_engine.sync_engine, "connect")
def set_async_sqlite_pragma(dbapi_connection, connection_record):
    """Set database connection parameters for async connections"""
    if "postgresql" in settings.database_url:
        # PostgreSQL specific settings
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET timezone TO 'UTC'")


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
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False