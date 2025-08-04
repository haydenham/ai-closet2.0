"""
Unit tests for database connection and basic operations
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import (
    Base,
    sync_engine,
    async_engine,
    SessionLocal,
    AsyncSessionLocal,
    get_async_session,
    get_sync_session,
    init_database,
    close_database,
    check_database_health,
)


class TestDatabaseConnection:
    """Test database connection and configuration"""
    
    def test_sync_engine_configuration(self):
        """Test synchronous engine configuration"""
        assert sync_engine is not None
        assert sync_engine.pool.size() == 10
        assert sync_engine.pool._max_overflow == 20
        assert sync_engine.pool._pre_ping is True
        assert sync_engine.pool._recycle == 3600
    
    def test_async_engine_configuration(self):
        """Test asynchronous engine configuration"""
        assert async_engine is not None
        assert async_engine.pool.size() == 10
        assert async_engine.pool._max_overflow == 20
        assert async_engine.pool._pre_ping is True
        assert async_engine.pool._recycle == 3600
    
    def test_base_class_exists(self):
        """Test that Base class is properly configured"""
        assert Base is not None
        assert hasattr(Base, 'metadata')
        assert hasattr(Base, 'registry')


class TestSessionManagement:
    """Test database session management"""
    
    def test_sync_session_creation(self):
        """Test synchronous session creation"""
        session = SessionLocal()
        assert session is not None
        # Check session configuration through the sessionmaker
        assert not SessionLocal.kw.get('autocommit', False)
        assert not SessionLocal.kw.get('autoflush', False)
        session.close()
    
    @pytest.mark.asyncio
    async def test_async_session_creation(self):
        """Test asynchronous session creation"""
        async with AsyncSessionLocal() as session:
            assert session is not None
            # Check session configuration through the sessionmaker
            assert not AsyncSessionLocal.kw.get('autocommit', False)
            assert not AsyncSessionLocal.kw.get('autoflush', False)
            assert not AsyncSessionLocal.kw.get('expire_on_commit', True)
    
    def test_sync_session_dependency(self):
        """Test synchronous session dependency function"""
        session_gen = get_sync_session()
        session = next(session_gen)
        assert session is not None
        
        # Test cleanup
        try:
            next(session_gen)
        except StopIteration:
            pass  # Expected behavior
    
    @pytest.mark.asyncio
    async def test_async_session_dependency(self):
        """Test asynchronous session dependency function"""
        async_gen = get_async_session()
        session = await async_gen.__anext__()
        assert session is not None
        
        # Test cleanup
        try:
            await async_gen.__anext__()
        except StopAsyncIteration:
            pass  # Expected behavior


class TestDatabaseOperations:
    """Test basic database operations"""
    
    @pytest.mark.asyncio
    async def test_database_initialization_success(self):
        """Test successful database initialization"""
        with patch('app.core.database.async_engine') as mock_async_engine, \
             patch('app.core.database.sync_engine') as mock_sync_engine:
            
            # Mock successful connections
            mock_async_conn = MagicMock()
            mock_sync_conn = MagicMock()
            
            mock_async_engine.begin.return_value.__aenter__.return_value = mock_async_conn
            mock_sync_engine.begin.return_value.__enter__.return_value = mock_sync_conn
            
            # Should not raise any exception
            await init_database()
    
    @pytest.mark.asyncio
    async def test_database_initialization_failure(self):
        """Test database initialization failure handling"""
        with patch('app.core.database.async_engine') as mock_async_engine:
            # Mock connection failure
            mock_async_engine.begin.side_effect = SQLAlchemyError("Connection failed")
            
            with pytest.raises(SQLAlchemyError):
                await init_database()
    
    @pytest.mark.asyncio
    async def test_database_closure_success(self):
        """Test successful database closure"""
        with patch('app.core.database.async_engine') as mock_async_engine, \
             patch('app.core.database.sync_engine') as mock_sync_engine:
            
            # Mock async dispose method
            mock_async_engine.dispose = AsyncMock()
            mock_sync_engine.dispose = MagicMock()
            
            await close_database()
            
            mock_async_engine.dispose.assert_called_once()
            mock_sync_engine.dispose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_database_closure_failure(self):
        """Test database closure failure handling"""
        with patch('app.core.database.async_engine') as mock_async_engine:
            # Mock disposal failure
            mock_async_engine.dispose = AsyncMock(side_effect=SQLAlchemyError("Disposal failed"))
            
            with pytest.raises(SQLAlchemyError):
                await close_database()
    
    @pytest.mark.asyncio
    async def test_database_health_check_success(self):
        """Test successful database health check"""
        with patch('app.core.database.async_engine') as mock_async_engine:
            # Mock successful connection and query
            mock_conn = AsyncMock()
            mock_async_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_async_engine.begin.return_value.__aexit__.return_value = None
            
            result = await check_database_health()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_database_health_check_failure(self):
        """Test database health check failure"""
        with patch('app.core.database.async_engine') as mock_async_engine:
            # Mock connection failure
            mock_async_engine.begin = AsyncMock(side_effect=SQLAlchemyError("Connection failed"))
            
            result = await check_database_health()
            assert result is False


class TestSessionContextManagers:
    """Test session context managers and error handling"""
    
    @pytest.mark.asyncio
    async def test_async_session_commit_on_success(self):
        """Test that async session commits on successful operation"""
        with patch('app.core.database.AsyncSessionLocal') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session_class.return_value.__aexit__.return_value = None
            
            async_gen = get_async_session()
            session = await async_gen.__anext__()
            
            # Simulate successful operation
            try:
                await async_gen.__anext__()
            except StopAsyncIteration:
                pass
            
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_async_session_rollback_on_error(self):
        """Test that async session rolls back on error"""
        with patch('app.core.database.AsyncSessionLocal') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session_class.return_value.__aexit__.return_value = None
            
            # Mock an exception during session use
            mock_session.commit.side_effect = SQLAlchemyError("Commit failed")
            
            async_gen = get_async_session()
            session = await async_gen.__anext__()
            
            with pytest.raises(SQLAlchemyError):
                try:
                    await async_gen.__anext__()
                except StopAsyncIteration:
                    pass
            
            mock_session.rollback.assert_called_once()
    
    def test_sync_session_commit_on_success(self):
        """Test that sync session commits on successful operation"""
        with patch('app.core.database.SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            session_gen = get_sync_session()
            session = next(session_gen)
            
            # Simulate successful operation
            try:
                next(session_gen)
            except StopIteration:
                pass
            
            mock_session.commit.assert_called_once()
    
    def test_sync_session_rollback_on_error(self):
        """Test that sync session rolls back on error"""
        with patch('app.core.database.SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock an exception during session use
            mock_session.commit.side_effect = SQLAlchemyError("Commit failed")
            
            session_gen = get_sync_session()
            session = next(session_gen)
            
            with pytest.raises(SQLAlchemyError):
                try:
                    next(session_gen)
                except StopIteration:
                    pass
            
            mock_session.rollback.assert_called_once()


class TestConnectionEventHandlers:
    """Test database connection event handlers"""
    
    @patch('app.core.database.settings')
    def test_postgresql_connection_settings(self, mock_settings):
        """Test PostgreSQL connection event handler"""
        mock_settings.database_url = "postgresql://user:pass@localhost/db"
        
        # Mock database connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Import and call the event handler
        from app.core.database import set_sqlite_pragma
        set_sqlite_pragma(mock_connection, None)
        
        # Verify timezone was set
        mock_cursor.execute.assert_called_once_with("SET timezone TO 'UTC'")
    
    @patch('app.core.database.settings')
    def test_non_postgresql_connection_settings(self, mock_settings):
        """Test that non-PostgreSQL connections don't trigger settings"""
        mock_settings.database_url = "sqlite:///test.db"
        
        # Mock database connection
        mock_connection = MagicMock()
        
        # Import and call the event handler
        from app.core.database import set_sqlite_pragma
        set_sqlite_pragma(mock_connection, None)
        
        # Verify no cursor operations were performed
        mock_connection.cursor.assert_not_called()


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()