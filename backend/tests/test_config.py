"""
Test configuration settings
"""
import pytest
from app.core.config import Settings


def test_settings_default_values():
    """Test that settings have correct default values"""
    settings = Settings()
    
    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30
    assert settings.smtp_port == 587
    assert settings.upload_dir == "uploads"
    assert settings.max_file_size == 10 * 1024 * 1024


def test_settings_from_env(monkeypatch):
    """Test that settings can be loaded from environment variables"""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    
    settings = Settings()
    
    assert settings.secret_key == "test-secret-key"
    assert settings.access_token_expire_minutes == 60