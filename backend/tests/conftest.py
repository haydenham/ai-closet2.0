"""
Pytest configuration and fixtures for unit testing
"""
import asyncio
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.database import Base, get_async_session
from app.main import app

# Create test database URLs - using in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
ASYNC_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engines
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

test_async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# Create test session makers
TestingSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=test_engine
)

TestingAsyncSessionLocal = async_sessionmaker(
    bind=test_async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_session():
    """Create test async database session for unit tests"""
    # Patch UUID for SQLite compatibility
    from tests.test_utils import patch_uuid_for_sqlite
    patch_uuid_for_sqlite()
    
    # Import all models to ensure they are registered
    from app.models.user import User, EmailVerificationToken, PasswordResetToken
    from app.models.style_profile import StyleProfile
    from app.models.clothing_item import ClothingItem
    from app.models.outfit_recommendation import OutfitRecommendation
    
    # Create tables for async engine
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingAsyncSessionLocal() as session:
        yield session
    
    # Clean up tables after each test
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def db_session():
    """Create test sync database session for unit tests"""
    # Patch UUID for SQLite compatibility
    from tests.test_utils import patch_uuid_for_sqlite
    patch_uuid_for_sqlite()
    
    # Import all models to ensure they are registered
    from app.models.user import User, EmailVerificationToken, PasswordResetToken
    from app.models.style_profile import StyleProfile
    from app.models.clothing_item import ClothingItem
    from app.models.outfit_recommendation import OutfitRecommendation
    
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        # Clean up tables after each test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
async def async_client(async_session: AsyncSession):
    """Create test async HTTP client with database dependency override"""
    
    async def override_get_async_session():
        """Override database session dependency for testing"""
        yield async_session
    
    # Override the database dependency
    app.dependency_overrides[get_async_session] = override_get_async_session
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Clean up dependency override
    app.dependency_overrides.clear()