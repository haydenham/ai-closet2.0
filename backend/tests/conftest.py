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
def client(db_session):
    """Create test sync HTTP client with database dependency override"""
    from app.core.database import get_sync_session
    
    def override_get_sync_session():
        """Override database session dependency for testing"""
        yield db_session
    
    # Override the database dependency
    app.dependency_overrides[get_sync_session] = override_get_sync_session
    
    with TestClient(app) as client:
        yield client
    
    # Clean up dependency override
    app.dependency_overrides.clear()


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


@pytest.fixture(scope="function")
async def authenticated_user(async_session: AsyncSession):
    """Create a test user for authentication tests"""
    from app.models.user import User
    from app.services.auth_service import auth_service
    
    # Create test user
    user_data = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    user = await auth_service.create_user(user_data, async_session)
    user.is_verified = True  # Mark as verified for testing
    await async_session.commit()
    await async_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def async_db_session(async_session):
    """Alias for async_session fixture for consistency"""
    return async_session


@pytest.fixture(scope="function")
async def test_user(async_session: AsyncSession):
    """Create a test user for user management tests"""
    from app.models.user import User
    from app.services.auth_service import auth_service
    from app.schemas.user import UserCreate
    from sqlalchemy import select
    import uuid
    
    # Create test user with unique email
    unique_id = str(uuid.uuid4())[:8]
    user_data = UserCreate(
        email=f"testuser{unique_id}@example.com",
        password="TestPassword123!",
        first_name="Test",
        last_name="User"
    )
    
    user_response, _ = await auth_service.register_user(user_data, async_session)
    # Get the actual user object from the database
    result = await async_session.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one()
    user.is_verified = True  # Mark as verified for testing
    await async_session.commit()
    await async_session.refresh(user)
    
    return user


async def create_auth_headers(user):
    """Helper function to create authentication headers for any user"""
    from app.services.auth_service import auth_service
    
    # Create access token for user
    tokens = await auth_service.create_user_tokens(user)
    
    return {
        "Authorization": f"Bearer {tokens.access_token}"
    }


@pytest.fixture(scope="function")
async def auth_headers(test_user):
    """Create authentication headers for test user"""
    return await create_auth_headers(test_user)


@pytest.fixture(scope="function")
async def test_user_with_style_profile(async_session: AsyncSession):
    """Create a test user with style profile"""
    from app.models.user import User
    from app.models.style_profile import StyleProfile
    from app.services.auth_service import auth_service
    from app.schemas.user import UserCreate
    from sqlalchemy import select
    import uuid
    
    # Create test user with unique email
    unique_id = str(uuid.uuid4())[:8]
    user_data = UserCreate(
        email=f"testuser{unique_id}@example.com",
        password="TestPassword123!",
        first_name="Test",
        last_name="User"
    )
    
    user_response, _ = await auth_service.register_user(user_data, async_session)
    # Get the actual user object from the database
    result = await async_session.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one()
    user.is_verified = True
    await async_session.commit()
    await async_session.refresh(user)
    
    # Create style profile
    style_profile = StyleProfile(
        user_id=user.id,
        quiz_responses={"gender": "female", "style": "casual"},
        assigned_model="casual_female_model",
        style_preferences=["casual", "comfortable"],
        fashion_goals=["versatility", "comfort"],
        preferred_colors=["blue", "black"],
        body_type="average",
        lifestyle="casual",
        budget_range="moderate"
    )
    
    async_session.add(style_profile)
    await async_session.commit()
    await async_session.refresh(style_profile)
    
    return user, style_profile


@pytest.fixture(scope="function")
async def test_user_with_data(async_session: AsyncSession):
    """Create a test user with clothing items and recommendations"""
    from app.models.user import User
    from app.models.clothing_item import ClothingItem
    from app.models.outfit_recommendation import OutfitRecommendation
    from app.services.auth_service import auth_service
    from app.schemas.user import UserCreate
    from sqlalchemy import select
    from datetime import datetime, timedelta
    import uuid
    
    # Create test user with unique email
    unique_id = str(uuid.uuid4())[:8]
    user_data = UserCreate(
        email=f"testuser{unique_id}@example.com",
        password="TestPassword123!",
        first_name="Test",
        last_name="User"
    )
    
    user_response, _ = await auth_service.register_user(user_data, async_session)
    # Get the actual user object from the database
    result = await async_session.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one()
    user.is_verified = True
    await async_session.commit()
    await async_session.refresh(user)
    
    # Create clothing items
    clothing_items = []
    categories = ["tops", "bottoms", "shoes"]
    
    for i, category in enumerate(categories):
        item = ClothingItem(
            user_id=user.id,
            filename=f"test_item_{i}.jpg",
            original_filename=f"test_item_{i}.jpg",
            category=category,
            image_url=f"https://example.com/test_{i}.jpg",
            embedding=[0.1 + i * 0.1] * 512,
            times_recommended=i + 1,
            upload_date=datetime.utcnow() - timedelta(days=i)
        )
        clothing_items.append(item)
        async_session.add(item)
    
    await async_session.commit()
    
    # Create outfit recommendations
    recommendations = []
    for i in range(3):
        rec = OutfitRecommendation(
            user_id=user.id,
            prompt=f"Test prompt {i}",
            ai_response=f"Test AI response {i}",
            ai_model_used="test_model",
            feedback_score=4 + (i % 2),  # Ratings of 4 or 5
            is_favorite=(i == 0),
            created_at=datetime.utcnow() - timedelta(days=i)
        )
        recommendations.append(rec)
        async_session.add(rec)
    
    await async_session.commit()
    
    # Refresh all objects
    for item in clothing_items:
        await async_session.refresh(item)
    for rec in recommendations:
        await async_session.refresh(rec)
    
    return user, clothing_items, recommendations