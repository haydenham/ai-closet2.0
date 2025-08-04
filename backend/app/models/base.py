"""
Base model class for SQLAlchemy models

This module is kept for backward compatibility.
New code should import from app.core.database instead.
"""
from app.core.database import Base, get_sync_session as get_db, get_async_session

# Re-export for backward compatibility
__all__ = ["Base", "get_db", "get_async_session"]