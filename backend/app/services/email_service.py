"""
Email service for sending verification and notification emails
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service class for sending emails"""
    
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
    
    def _create_smtp_connection(self) -> Optional[smtplib.SMTP]:
        """Create SMTP connection"""
        if not all([self.smtp_server, self.smtp_username, self.smtp_password]):
            logger.warning("SMTP configuration incomplete, email sending disabled")
            return None
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            return None
    
    def send_verification_email(self, email: str, first_name: str, verification_token: str) -> bool:
        """
        Send email verification email
        
        Args:
            email: Recipient email address
            first_name: User's first name
            verification_token: Email verification token
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.smtp_server:
            logger.info(f"Email sending disabled. Verification token for {email}: {verification_token}")
            return True  # Return True in development mode
        
        try:
            server = self._create_smtp_connection()
            if not server:
                return False
            
            # Create email content
            subject = "Verify Your Fashion AI Platform Account"
            
            # Create verification URL (in production, this would be your frontend URL)
            verification_url = f"http://localhost:3000/verify-email?token={verification_token}"
            
            html_body = f"""
            <html>
                <body>
                    <h2>Welcome to Fashion AI Platform!</h2>
                    <p>Hi {first_name},</p>
                    <p>Thank you for registering with Fashion AI Platform. To complete your registration, please verify your email address by clicking the link below:</p>
                    <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email Address</a></p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p>{verification_url}</p>
                    <p>This verification link will expire in 24 hours.</p>
                    <p>If you didn't create an account with us, please ignore this email.</p>
                    <br>
                    <p>Best regards,<br>The Fashion AI Platform Team</p>
                </body>
            </html>
            """
            
            text_body = f"""
            Welcome to Fashion AI Platform!
            
            Hi {first_name},
            
            Thank you for registering with Fashion AI Platform. To complete your registration, please verify your email address by visiting this link:
            
            {verification_url}
            
            This verification link will expire in 24 hours.
            
            If you didn't create an account with us, please ignore this email.
            
            Best regards,
            The Fashion AI Platform Team
            """
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_username
            msg["To"] = email
            
            # Add both text and HTML parts
            text_part = MIMEText(text_body, "plain")
            html_part = MIMEText(html_body, "html")
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Verification email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {e}")
            return False
    
    def send_password_reset_email(self, email: str, first_name: str, reset_token: str) -> bool:
        """
        Send password reset email
        
        Args:
            email: Recipient email address
            first_name: User's first name
            reset_token: Password reset token
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.smtp_server:
            logger.info(f"Email sending disabled. Password reset token for {email}: {reset_token}")
            return True  # Return True in development mode
        
        try:
            server = self._create_smtp_connection()
            if not server:
                return False
            
            # Create email content
            subject = "Reset Your Fashion AI Platform Password"
            
            # Create reset URL (in production, this would be your frontend URL)
            reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
            
            html_body = f"""
            <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Hi {first_name},</p>
                    <p>We received a request to reset your password for your Fashion AI Platform account.</p>
                    <p>Click the link below to reset your password:</p>
                    <p><a href="{reset_url}" style="background-color: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p>{reset_url}</p>
                    <p>This reset link will expire in 1 hour.</p>
                    <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                    <br>
                    <p>Best regards,<br>The Fashion AI Platform Team</p>
                </body>
            </html>
            """
            
            text_body = f"""
            Password Reset Request
            
            Hi {first_name},
            
            We received a request to reset your password for your Fashion AI Platform account.
            
            Visit this link to reset your password:
            {reset_url}
            
            This reset link will expire in 1 hour.
            
            If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
            
            Best regards,
            The Fashion AI Platform Team
            """
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_username
            msg["To"] = email
            
            # Add both text and HTML parts
            text_part = MIMEText(text_body, "plain")
            html_part = MIMEText(html_body, "html")
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Password reset email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
            return False


# Create a global instance
email_service = EmailService()