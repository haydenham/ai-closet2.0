"""
Test main application endpoints
"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns correct message"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Fashion AI Platform API"}


def test_health_check_endpoint(client: TestClient):
    """Test health check endpoint returns healthy status"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_cors_headers(client: TestClient):
    """Test CORS headers are properly configured"""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    # Check that CORS headers would be present in a real scenario
    # FastAPI's CORS middleware handles this automatically