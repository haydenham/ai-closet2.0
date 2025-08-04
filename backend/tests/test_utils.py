"""
Test utilities and custom types for testing
"""
import uuid
from sqlalchemy import TypeDecorator, String
from sqlalchemy.dialects import sqlite


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


# Monkey patch UUID for SQLite in tests
def patch_uuid_for_sqlite():
    """Patch UUID type to work with SQLite in tests"""
    from sqlalchemy import UUID
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
    
    def visit_UUID(self, type_, **kw):
        return "CHAR(36)"
    
    SQLiteTypeCompiler.visit_UUID = visit_UUID