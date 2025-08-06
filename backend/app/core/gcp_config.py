"""
Google Cloud Platform specific configuration
"""
import os
from typing import Optional

try:
    from google.cloud import secretmanager
    HAS_GCP = True
except ImportError:
    HAS_GCP = False
    secretmanager = None


class GCPConfig:
    """GCP-specific configuration management"""
    
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.secret_client = None
        
        if self.project_id and HAS_GCP:
            try:
                self.secret_client = secretmanager.SecretManagerServiceClient()
            except Exception:
                # Fallback to environment variables if Secret Manager is not available
                pass
    
    def get_secret(self, secret_name: str, version: str = "latest") -> Optional[str]:
        """Get secret from Google Secret Manager"""
        if not self.secret_client or not self.project_id:
            return os.getenv(secret_name)
        
        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception:
            # Fallback to environment variable
            return os.getenv(secret_name)
    
    def get_database_url(self) -> str:
        """Get database URL for Cloud SQL"""
        # For Cloud SQL, we can use either:
        # 1. Unix socket connection (recommended for Cloud Run)
        # 2. TCP connection with Cloud SQL Proxy
        
        if os.getenv('CLOUD_SQL_CONNECTION_NAME'):
            # Unix socket connection for Cloud Run
            db_user = self.get_secret('DB_USER') or 'postgres'
            db_pass = self.get_secret('DB_PASSWORD')
            db_name = self.get_secret('DB_NAME') or 'fashion_ai'
            connection_name = os.getenv('CLOUD_SQL_CONNECTION_NAME')
            
            return f"postgresql://{db_user}:{db_pass}@/{db_name}?host=/cloudsql/{connection_name}"
        else:
            # Fallback to regular connection
            return self.get_secret('DATABASE_URL') or os.getenv('DATABASE_URL')
    
    def get_storage_bucket(self) -> Optional[str]:
        """Get Google Cloud Storage bucket name"""
        return self.get_secret('GCS_BUCKET_NAME') or os.getenv('GCS_BUCKET_NAME')