"""
Tests for email service
"""
import pytest
from unittest.mock import patch, MagicMock
import smtplib

from app.services.email_service import EmailService


class TestEmailService:
    """Test cases for EmailService"""
    
    @pytest.fixture
    def email_service(self):
        """Create EmailService instance for testing"""
        return EmailService()
    
    @pytest.fixture
    def mock_smtp_settings(self):
        """Mock SMTP settings"""
        return {
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'smtp_username': 'test@example.com',
            'smtp_password': 'password123'
        }
    
    def test_email_service_initialization(self, email_service):
        """Test EmailService initialization"""
        assert email_service.smtp_server is None  # Default from settings
        assert email_service.smtp_port == 587
        assert email_service.smtp_username is None
        assert email_service.smtp_password is None
    
    @patch('app.services.email_service.smtplib.SMTP')
    def test_create_smtp_connection_success(self, mock_smtp_class, email_service, mock_smtp_settings):
        """Test successful SMTP connection creation"""
        # Mock SMTP instance
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        
        # Set up email service with mock settings
        for key, value in mock_smtp_settings.items():
            setattr(email_service, key, value)
        
        # Test connection creation
        connection = email_service._create_smtp_connection()
        
        assert connection is not None
        mock_smtp_class.assert_called_once_with('smtp.example.com', 587)
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with('test@example.com', 'password123')
    
    def test_create_smtp_connection_incomplete_config(self, email_service):
        """Test SMTP connection with incomplete configuration"""
        # Default settings should be incomplete
        connection = email_service._create_smtp_connection()
        assert connection is None
    
    @patch('app.services.email_service.smtplib.SMTP')
    def test_create_smtp_connection_failure(self, mock_smtp_class, email_service, mock_smtp_settings):
        """Test SMTP connection failure"""
        # Mock SMTP to raise exception
        mock_smtp_class.side_effect = smtplib.SMTPException("Connection failed")
        
        # Set up email service with mock settings
        for key, value in mock_smtp_settings.items():
            setattr(email_service, key, value)
        
        connection = email_service._create_smtp_connection()
        assert connection is None
    
    @patch('app.services.email_service.EmailService._create_smtp_connection')
    def test_send_verification_email_success(self, mock_create_connection, email_service):
        """Test successful verification email sending"""
        # Mock SMTP connection
        mock_smtp = MagicMock()
        mock_create_connection.return_value = mock_smtp
        
        # Set up email service with SMTP server (to avoid development mode)
        email_service.smtp_server = 'smtp.example.com'
        
        result = email_service.send_verification_email(
            email="test@example.com",
            first_name="John",
            verification_token="test_token_123"
        )
        
        assert result is True
        mock_create_connection.assert_called_once()
        mock_smtp.send_message.assert_called_once()
        mock_smtp.quit.assert_called_once()
        
        # Verify email content
        call_args = mock_smtp.send_message.call_args[0][0]
        assert call_args["Subject"] == "Verify Your Fashion AI Platform Account"
        assert call_args["From"] == email_service.smtp_username
        assert call_args["To"] == "test@example.com"
    
    def test_send_verification_email_development_mode(self, email_service):
        """Test verification email in development mode (no SMTP server)"""
        # Default settings should have no SMTP server
        result = email_service.send_verification_email(
            email="test@example.com",
            first_name="John",
            verification_token="test_token_123"
        )
        
        # Should return True in development mode
        assert result is True
    
    @patch('app.services.email_service.EmailService._create_smtp_connection')
    def test_send_verification_email_connection_failure(self, mock_create_connection, email_service):
        """Test verification email sending with connection failure"""
        mock_create_connection.return_value = None
        email_service.smtp_server = 'smtp.example.com'
        
        result = email_service.send_verification_email(
            email="test@example.com",
            first_name="John",
            verification_token="test_token_123"
        )
        
        assert result is False
    
    @patch('app.services.email_service.EmailService._create_smtp_connection')
    def test_send_verification_email_smtp_exception(self, mock_create_connection, email_service):
        """Test verification email sending with SMTP exception"""
        mock_smtp = MagicMock()
        mock_smtp.send_message.side_effect = smtplib.SMTPException("Send failed")
        mock_create_connection.return_value = mock_smtp
        email_service.smtp_server = 'smtp.example.com'
        
        result = email_service.send_verification_email(
            email="test@example.com",
            first_name="John",
            verification_token="test_token_123"
        )
        
        assert result is False
    
    @patch('app.services.email_service.EmailService._create_smtp_connection')
    def test_send_password_reset_email_success(self, mock_create_connection, email_service):
        """Test successful password reset email sending"""
        # Mock SMTP connection
        mock_smtp = MagicMock()
        mock_create_connection.return_value = mock_smtp
        
        # Set up email service with SMTP server
        email_service.smtp_server = 'smtp.example.com'
        
        result = email_service.send_password_reset_email(
            email="test@example.com",
            first_name="John",
            reset_token="reset_token_123"
        )
        
        assert result is True
        mock_create_connection.assert_called_once()
        mock_smtp.send_message.assert_called_once()
        mock_smtp.quit.assert_called_once()
        
        # Verify email content
        call_args = mock_smtp.send_message.call_args[0][0]
        assert call_args["Subject"] == "Reset Your Fashion AI Platform Password"
        assert call_args["From"] == email_service.smtp_username
        assert call_args["To"] == "test@example.com"
    
    def test_send_password_reset_email_development_mode(self, email_service):
        """Test password reset email in development mode"""
        result = email_service.send_password_reset_email(
            email="test@example.com",
            first_name="John",
            reset_token="reset_token_123"
        )
        
        # Should return True in development mode
        assert result is True
    
    @patch('app.services.email_service.EmailService._create_smtp_connection')
    def test_send_password_reset_email_connection_failure(self, mock_create_connection, email_service):
        """Test password reset email with connection failure"""
        mock_create_connection.return_value = None
        email_service.smtp_server = 'smtp.example.com'
        
        result = email_service.send_password_reset_email(
            email="test@example.com",
            first_name="John",
            reset_token="reset_token_123"
        )
        
        assert result is False
    
    @patch('app.services.email_service.EmailService._create_smtp_connection')
    def test_email_content_verification(self, mock_create_connection, email_service):
        """Test verification email content includes required elements"""
        mock_smtp = MagicMock()
        mock_create_connection.return_value = mock_smtp
        email_service.smtp_server = 'smtp.example.com'
        
        email_service.send_verification_email(
            email="john.doe@example.com",
            first_name="John",
            verification_token="abc123xyz"
        )
        
        # Get the message that was sent
        call_args = mock_smtp.send_message.call_args[0][0]
        message_content = str(call_args)
        
        # Verify required content is present
        assert "John" in message_content  # First name
        assert "abc123xyz" in message_content  # Token
        assert "verify" in message_content.lower()  # Verification purpose
        assert "http://localhost:3000/verify-email?token=abc123xyz" in message_content  # Verification URL
        assert "24 hours" in message_content  # Expiration time
    
    @patch('app.services.email_service.EmailService._create_smtp_connection')
    def test_email_content_password_reset(self, mock_create_connection, email_service):
        """Test password reset email content includes required elements"""
        mock_smtp = MagicMock()
        mock_create_connection.return_value = mock_smtp
        email_service.smtp_server = 'smtp.example.com'
        
        email_service.send_password_reset_email(
            email="jane.doe@example.com",
            first_name="Jane",
            reset_token="reset456def"
        )
        
        # Get the message that was sent
        call_args = mock_smtp.send_message.call_args[0][0]
        message_content = str(call_args)
        
        # Verify required content is present
        assert "Jane" in message_content  # First name
        assert "reset456def" in message_content  # Token
        assert "reset" in message_content.lower()  # Reset purpose
        assert "http://localhost:3000/reset-password?token=reset456def" in message_content  # Reset URL
        assert "1 hour" in message_content  # Expiration time
    
    @patch('app.services.email_service.EmailService._create_smtp_connection')
    def test_email_multipart_structure(self, mock_create_connection, email_service):
        """Test that emails are sent with both HTML and text parts"""
        mock_smtp = MagicMock()
        mock_create_connection.return_value = mock_smtp
        email_service.smtp_server = 'smtp.example.com'
        
        email_service.send_verification_email(
            email="test@example.com",
            first_name="Test",
            verification_token="token123"
        )
        
        # Get the message that was sent
        call_args = mock_smtp.send_message.call_args[0][0]
        
        # Verify it's a multipart message
        assert call_args.is_multipart()
        
        # Get parts
        parts = call_args.get_payload()
        assert len(parts) == 2  # Should have text and HTML parts
        
        # Verify content types
        content_types = [part.get_content_type() for part in parts]
        assert "text/plain" in content_types
        assert "text/html" in content_types