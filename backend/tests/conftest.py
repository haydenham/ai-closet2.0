"""
Pytest configuration and fixtures
"""
import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from unittest.mock import patch

from app.main import app
from app.core.database import Base, get_sync_session, get_async_session

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


def override_get_sync_db():
    """Override sync database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def override_get_async_db():
    """Override async database dependency for testing"""
    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine and tables"""
    # Patch UUID for SQLite compatibility
    from tests.test_utils import patch_uuid_for_sqlite
    patch_uuid_for_sqlite()
    
    # Import all models to ensure they are registered
    from app.models import User, StyleProfile, ClothingItem, OutfitRecommendation
    
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    yield test_engine
    
    # Drop tables
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create test database session"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
async def async_db_session():
    """Create test async database session"""
    async with TestingAsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
def client():
    """Create test client with database override"""
    # Mock all database operations to avoid actual database calls during testing
    with patch('app.main.init_database') as mock_init, \
         patch('app.main.close_database') as mock_close, \
         patch('app.main.check_database_health', return_value=True) as mock_health:
        
        # Configure mocks
        mock_init.return_value = None
        mock_close.return_value = None
        
        # Override database dependencies
        app.dependency_overrides[get_sync_session] = override_get_sync_db
        app.dependency_overrides[get_async_session] = override_get_async_db
        
        with TestClient(app) as test_client:
            yield test_client
        
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_database_operations():
    """Mock database operations for unit tests"""
    with patch('app.core.database.init_database') as mock_init, \
         patch('app.core.database.close_database') as mock_close, \
         patch('app.core.database.check_database_health') as mock_health:
        
        mock_init.return_value = None
        mock_close.return_value = None
        mock_health.return_value = True
        
        yield {
            'init': mock_init,
            'close': mock_close,
            'health': mock_health
        }