"""
Comprehensive security tests including penetration testing scenarios
"""
import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException

from app.core.security import (
    InputSanitizer, FileValidator, RateLimiter, SecurityConfig,
    validate_no_sql_injection, validate_no_xss, validate_safe_filename
)
from app.schemas.security import (
    SecureUserCreate, SecureUserLogin, SecureClothingItemUpload,
    SecureOutfitRequest, SecureRecommendationFeedback, SecureSearchQuery
)


class TestInputSanitizer:
    """Test input sanitization functionality"""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization"""
        result = InputSanitizer.sanitize_string("Hello World")
        assert result == "Hello World"
    
    def test_sanitize_string_html_escape(self):
        """Test HTML escaping"""
        result = InputSanitizer.sanitize_string("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result
    
    def test_sanitize_string_control_chars(self):
        """Test removal of control characters"""
        result = InputSanitizer.sanitize_string("Hello\x00\x01World\x7f")
        assert result == "HelloWorld"
    
    def test_sanitize_string_length_limit(self):
        """Test string length validation"""
        with pytest.raises(ValueError, match="String too long"):
            InputSanitizer.sanitize_string("a" * 1000, max_length=100)
    
    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization"""
        result = InputSanitizer.sanitize_filename("test_file.jpg")
        assert result == "test_file.jpg"
    
    def test_sanitize_filename_dangerous_chars(self):
        """Test removal of dangerous characters from filename"""
        result = InputSanitizer.sanitize_filename("../../../etc/passwd")
        assert result == "etcpasswd"
    
    def test_sanitize_filename_reserved_names(self):
        """Test handling of reserved Windows filenames"""
        result = InputSanitizer.sanitize_filename("CON.txt")
        assert result.startswith("file_CON.txt")
    
    def test_sanitize_filename_empty(self):
        """Test handling of empty filename"""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            InputSanitizer.sanitize_filename("")
    
    def test_detect_sql_injection_positive(self):
        """Test SQL injection detection - positive cases"""
        test_cases = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM passwords",
            "admin'--",
            "1; DELETE FROM users",
            "' OR 1=1 --"
        ]
        
        for case in test_cases:
            assert InputSanitizer.detect_sql_injection(case), f"Failed to detect SQL injection in: {case}"
    
    def test_detect_sql_injection_negative(self):
        """Test SQL injection detection - negative cases"""
        test_cases = [
            "normal text",
            "user@example.com",
            "My favorite color is blue",
            "I like SQL databases",
            "Order by date"
        ]
        
        for case in test_cases:
            assert not InputSanitizer.detect_sql_injection(case), f"False positive for: {case}"
    
    def test_detect_xss_positive(self):
        """Test XSS detection - positive cases"""
        test_cases = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "onload=alert('xss')",
            "<object data='javascript:alert(1)'></object>"
        ]
        
        for case in test_cases:
            assert InputSanitizer.detect_xss(case), f"Failed to detect XSS in: {case}"
    
    def test_detect_xss_negative(self):
        """Test XSS detection - negative cases"""
        test_cases = [
            "normal text",
            "I love JavaScript programming",
            "Check out this script for automation",
            "The iframe element is useful",
            "Loading data..."
        ]
        
        for case in test_cases:
            assert not InputSanitizer.detect_xss(case), f"False positive for: {case}"


class TestSecuritySchemas:
    """Test security-enhanced Pydantic schemas"""
    
    def test_secure_user_create_valid(self):
        """Test valid user creation"""
        user_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecurePass123!"
        }
        
        user = SecureUserCreate(**user_data)
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
    
    def test_secure_user_create_invalid_name(self):
        """Test user creation with invalid name characters"""
        user_data = {
            "email": "test@example.com",
            "first_name": "John<script>",
            "last_name": "Doe",
            "password": "SecurePass123!"
        }
        
        with pytest.raises(ValueError, match="Name contains invalid characters"):
            SecureUserCreate(**user_data)
    
    def test_secure_user_create_weak_password(self):
        """Test user creation with weak password"""
        user_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "weak"
        }
        
        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            SecureUserCreate(**user_data)
    
    def test_secure_user_create_common_password(self):
        """Test user creation with common password"""
        user_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "password123"
        }
        
        with pytest.raises(ValueError, match="Password is too common"):
            SecureUserCreate(**user_data)


class TestPenetrationTestingScenarios:
    """Penetration testing scenarios for security validation"""
    
    def test_sql_injection_attempts(self):
        """Test various SQL injection attack vectors"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/*",
            "' UNION SELECT * FROM passwords --",
            "1; DELETE FROM users WHERE 1=1 --",
            "' OR 1=1#",
            "1' AND (SELECT COUNT(*) FROM users) > 0 --"
        ]
        
        for payload in sql_payloads:
            # Test that SQL injection is detected
            assert InputSanitizer.detect_sql_injection(payload), f"SQL injection not detected: {payload}"
    
    def test_xss_attempts(self):
        """Test various XSS attack vectors"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<svg onload=alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>"
        ]
        
        for payload in xss_payloads:
            # Test that XSS is detected
            assert InputSanitizer.detect_xss(payload), f"XSS not detected: {payload}"
    
    def test_path_traversal_attempts(self):
        """Test path traversal attack vectors"""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
        ]
        
        for payload in traversal_payloads:
            # Test that filename sanitization removes dangerous paths
            sanitized = InputSanitizer.sanitize_filename(payload)
            assert "../" not in sanitized and "..\\" not in sanitized, f"Path traversal not sanitized: {payload}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])