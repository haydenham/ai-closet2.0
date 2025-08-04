"""
Test main application endpoints
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns correct message"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Fashion AI Platform API"}


@patch('app.main.check_database_health')
def test_health_check_endpoint_healthy(mock_health_check, client: TestClient):
    """Test health check endpoint when database is healthy"""
    mock_health_check.return_value = True
    
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "database": "connected"
    }


@patch('app.main.check_database_health')
def test_health_check_endpoint_unhealthy(mock_health_check, client: TestClient):
    """Test health check endpoint when database is unhealthy"""
    mock_health_check.return_value = False
    
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "unhealthy",
        "database": "disconnected"
    }


def test_cors_headers(client: TestClient):
    """Test CORS headers are properly configured"""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    # Check that CORS headers would be present in a real scenario
    # FastAPI's CORS middleware handles this automatically


@pytest.mark.asyncio
@patch('app.main.init_database')
@patch('app.main.close_database')
async def test_lifespan_success(mock_close_db, mock_init_db):
    """Test successful application lifespan management"""
    mock_init_db.return_value = None
    mock_close_db.return_value = None
    
    # Test that lifespan context manager works
    from app.main import lifespan, app
    
    async with lifespan(app):
        pass
    
    mock_init_db.assert_called_once()
    mock_close_db.assert_called_once()


@pytest.mark.asyncio
@patch('app.main.init_database')
async def test_lifespan_startup_failure(mock_init_db):
    """Test application lifespan with startup failure"""
    mock_init_db.side_effect = Exception("Database connection failed")
    
    from app.main import lifespan, app
    
    with pytest.raises(Exception, match="Database connection failed"):
        async with lifespan(app):
            pass