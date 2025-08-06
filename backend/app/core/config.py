"""
Application configuration settings
"""
import os
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings
from typing import Optional

from app.core.gcp_config import GCPConfig


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")
    
    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/fashion_ai"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Email
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Google Cloud
    google_cloud_project: Optional[str] = None
    google_cloud_credentials_path: Optional[str] = None
    cloud_sql_connection_name: Optional[str] = None
    gcs_bucket_name: Optional[str] = None
    
    # File Storage
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "https://your-frontend-domain.com"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize GCP config if running in Google Cloud
        if self.google_cloud_project or os.getenv('GOOGLE_CLOUD_PROJECT'):
            gcp_config = GCPConfig(self.google_cloud_project)
            
            # Override database URL for Cloud SQL if available
            cloud_sql_url = gcp_config.get_database_url()
            if cloud_sql_url and cloud_sql_url != self.database_url:
                self.database_url = cloud_sql_url
            
            # Set GCS bucket if available
            if not self.gcs_bucket_name:
                self.gcs_bucket_name = gcp_config.get_storage_bucket()
            
            # Get secrets from Secret Manager
            if not self.secret_key or self.secret_key == "your-secret-key-change-in-production":
                secret_key = gcp_config.get_secret('JWT_SECRET_KEY')
                if secret_key:
                    self.secret_key = secret_key
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"


settings = Settings()