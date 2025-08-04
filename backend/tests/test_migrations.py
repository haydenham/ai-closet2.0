"""
Integration tests for database migrations
"""
import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import patch, MagicMock

from app.core.migration_utils import MigrationManager, run_migration_tests
from app.core.database import Base
from app.models.user import User, EmailVerificationToken, PasswordResetToken
from app.models.style_profile import StyleProfile, QuizQuestion
from app.models.clothing_item import ClothingItem, ClothingCategory
from app.models.outfit_recommendation import OutfitRecommendation, RecommendationFeedback


class TestMigrationManager:
    """Test cases for MigrationManager class"""
    
    @pytest.fixture
    def temp_db_url(self):
        """Create temporary SQLite database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"
            yield db_url
            # Cleanup
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
    
    @pytest.fixture
    def migration_manager(self, temp_db_url):
        """Create MigrationManager instance with temporary database"""
        return MigrationManager(database_url=temp_db_url)
    
    def test_migration_manager_initialization(self, migration_manager):
        """Test MigrationManager initialization"""
        assert migration_manager.database_url.startswith("sqlite:///")
        assert migration_manager.alembic_cfg_path.exists()
    
    def test_get_alembic_config(self, migration_manager):
        """Test Alembic configuration retrieval"""
        config = migration_manager.get_alembic_config()
        assert config is not None
        assert config.get_main_option("sqlalchemy.url") == migration_manager.database_url
    
    @patch('app.core.migration_utils.create_engine')
    @patch('app.core.migration_utils.MigrationContext')
    def test_get_current_revision_success(self, mock_context, mock_engine, migration_manager):
        """Test successful current revision retrieval"""
        # Setup mocks
        mock_connection = MagicMock()
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_connection
        mock_migration_context = MagicMock()
        mock_migration_context.get_current_revision.return_value = "abc123"
        mock_context.configure.return_value = mock_migration_context
        
        # Test
        revision = migration_manager.get_current_revision()
        
        # Assertions
        assert revision == "abc123"
        mock_engine.assert_called_once_with(migration_manager.database_url)
        mock_context.configure.assert_called_once_with(mock_connection)
    
    @patch('app.core.migration_utils.create_engine')
    def test_get_current_revision_failure(self, mock_engine, migration_manager):
        """Test current revision retrieval failure"""
        # Setup mock to raise exception
        mock_engine.side_effect = SQLAlchemyError("Connection failed")
        
        # Test
        revision = migration_manager.get_current_revision()
        
        # Assertions
        assert revision is None
    
    @patch('app.core.migration_utils.ScriptDirectory')
    def test_get_available_revisions_success(self, mock_script_dir, migration_manager):
        """Test successful available revisions retrieval"""
        # Setup mocks
        mock_revision1 = MagicMock()
        mock_revision1.revision = "rev1"
        mock_revision2 = MagicMock()
        mock_revision2.revision = "rev2"
        
        mock_script = MagicMock()
        mock_script.walk_revisions.return_value = [mock_revision1, mock_revision2]
        mock_script_dir.from_config.return_value = mock_script
        
        # Test
        revisions = migration_manager.get_available_revisions()
        
        # Assertions
        assert revisions == ["rev1", "rev2"]
        mock_script_dir.from_config.assert_called_once()
    
    @patch('app.core.migration_utils.ScriptDirectory')
    def test_get_available_revisions_failure(self, mock_script_dir, migration_manager):
        """Test available revisions retrieval failure"""
        # Setup mock to raise exception
        mock_script_dir.from_config.side_effect = Exception("Script error")
        
        # Test
        revisions = migration_manager.get_available_revisions()
        
        # Assertions
        assert revisions == []
    
    def test_check_migration_status_no_revisions(self, migration_manager):
        """Test migration status check with no revisions"""
        with patch.object(migration_manager, 'get_current_revision', return_value=None), \
             patch.object(migration_manager, 'get_available_revisions', return_value=[]):
            
            status = migration_manager.check_migration_status()
            
            assert status["current_revision"] is None
            assert status["available_revisions"] == []
            assert status["is_up_to_date"] is False
            assert status["pending_migrations"] == []
    
    def test_check_migration_status_up_to_date(self, migration_manager):
        """Test migration status check when up to date"""
        with patch.object(migration_manager, 'get_current_revision', return_value="rev1"), \
             patch.object(migration_manager, 'get_available_revisions', return_value=["rev1", "rev2"]):
            
            status = migration_manager.check_migration_status()
            
            assert status["current_revision"] == "rev1"
            assert status["available_revisions"] == ["rev1", "rev2"]
            assert status["is_up_to_date"] is True
            assert status["pending_migrations"] == []
    
    def test_check_migration_status_pending_migrations(self, migration_manager):
        """Test migration status check with pending migrations"""
        with patch.object(migration_manager, 'get_current_revision', return_value="rev2"), \
             patch.object(migration_manager, 'get_available_revisions', return_value=["rev1", "rev2", "rev3"]):
            
            status = migration_manager.check_migration_status()
            
            assert status["current_revision"] == "rev2"
            assert status["available_revisions"] == ["rev1", "rev2", "rev3"]
            assert status["is_up_to_date"] is False
            assert status["pending_migrations"] == ["rev1"]
    
    @patch('app.core.migration_utils.command')
    def test_upgrade_database_success(self, mock_command, migration_manager):
        """Test successful database upgrade"""
        # Test
        result = migration_manager.upgrade_database("head")
        
        # Assertions
        assert result is True
        mock_command.upgrade.assert_called_once()
    
    @patch('app.core.migration_utils.command')
    def test_upgrade_database_failure(self, mock_command, migration_manager):
        """Test database upgrade failure"""
        # Setup mock to raise exception
        mock_command.upgrade.side_effect = Exception("Upgrade failed")
        
        # Test
        result = migration_manager.upgrade_database("head")
        
        # Assertions
        assert result is False
    
    @patch('app.core.migration_utils.command')
    def test_downgrade_database_success(self, mock_command, migration_manager):
        """Test successful database downgrade"""
        # Test
        result = migration_manager.downgrade_database("base")
        
        # Assertions
        assert result is True
        mock_command.downgrade.assert_called_once()
    
    @patch('app.core.migration_utils.command')
    def test_downgrade_database_failure(self, mock_command, migration_manager):
        """Test database downgrade failure"""
        # Setup mock to raise exception
        mock_command.downgrade.side_effect = Exception("Downgrade failed")
        
        # Test
        result = migration_manager.downgrade_database("base")
        
        # Assertions
        assert result is False
    
    @patch('app.core.migration_utils.command')
    def test_create_migration_success(self, mock_command, migration_manager):
        """Test successful migration creation"""
        # Test
        result = migration_manager.create_migration("Test migration", autogenerate=True)
        
        # Assertions
        assert result is True
        mock_command.revision.assert_called_once()
    
    @patch('app.core.migration_utils.command')
    def test_create_migration_failure(self, mock_command, migration_manager):
        """Test migration creation failure"""
        # Setup mock to raise exception
        mock_command.revision.side_effect = Exception("Creation failed")
        
        # Test
        result = migration_manager.create_migration("Test migration")
        
        # Assertions
        assert result is False
    
    def test_validate_migration_success(self, migration_manager):
        """Test successful migration validation"""
        with patch.object(migration_manager, 'get_current_revision', return_value="base"), \
             patch.object(migration_manager, 'upgrade_database', return_value=True), \
             patch.object(migration_manager, 'downgrade_database', return_value=True):
            
            result = migration_manager.validate_migration("rev1")
            
            assert result["revision"] == "rev1"
            assert result["upgrade_success"] is True
            assert result["downgrade_success"] is True
            assert result["errors"] == []
    
    def test_validate_migration_upgrade_failure(self, migration_manager):
        """Test migration validation with upgrade failure"""
        with patch.object(migration_manager, 'get_current_revision', return_value="base"), \
             patch.object(migration_manager, 'upgrade_database', return_value=False):
            
            result = migration_manager.validate_migration("rev1")
            
            assert result["revision"] == "rev1"
            assert result["upgrade_success"] is False
            assert result["downgrade_success"] is False
            assert "Upgrade failed" in result["errors"]
    
    def test_validate_migration_downgrade_failure(self, migration_manager):
        """Test migration validation with downgrade failure"""
        with patch.object(migration_manager, 'get_current_revision', return_value="base"), \
             patch.object(migration_manager, 'upgrade_database', return_value=True), \
             patch.object(migration_manager, 'downgrade_database', return_value=False):
            
            result = migration_manager.validate_migration("rev1")
            
            assert result["revision"] == "rev1"
            assert result["upgrade_success"] is True
            assert result["downgrade_success"] is False
            assert any("Downgrade" in error for error in result["errors"])
    
    @patch('app.core.migration_utils.inspect')
    @patch('app.core.migration_utils.create_engine')
    def test_check_database_schema_success(self, mock_engine, mock_inspect, migration_manager):
        """Test successful database schema check"""
        # Setup mocks
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["users", "posts"]
        mock_inspector.get_columns.return_value = [
            {"name": "id", "type": "INTEGER", "nullable": False, "default": None},
            {"name": "email", "type": "VARCHAR", "nullable": False, "default": None}
        ]
        mock_inspector.get_indexes.return_value = [
            {"name": "ix_users_email", "column_names": ["email"], "unique": True}
        ]
        mock_inspector.get_foreign_keys.return_value = []
        mock_inspect.return_value = mock_inspector
        
        # Test
        schema = migration_manager.check_database_schema()
        
        # Assertions
        assert "tables" in schema
        assert "table_details" in schema
        assert schema["tables"] == ["users", "posts"]
        assert "users" in schema["table_details"]
        assert "posts" in schema["table_details"]
    
    @patch('app.core.migration_utils.create_engine')
    def test_check_database_schema_failure(self, mock_engine, migration_manager):
        """Test database schema check failure"""
        # Setup mock to raise exception
        mock_engine.side_effect = SQLAlchemyError("Connection failed")
        
        # Test
        schema = migration_manager.check_database_schema()
        
        # Assertions
        assert "error" in schema
    
    def test_reset_database_success(self, migration_manager):
        """Test successful database reset"""
        with patch.object(migration_manager, 'downgrade_database', return_value=True), \
             patch.object(migration_manager, 'upgrade_database', return_value=True):
            
            result = migration_manager.reset_database()
            
            assert result is True
    
    def test_reset_database_downgrade_failure(self, migration_manager):
        """Test database reset with downgrade failure"""
        with patch.object(migration_manager, 'downgrade_database', return_value=False):
            
            result = migration_manager.reset_database()
            
            assert result is False
    
    def test_reset_database_upgrade_failure(self, migration_manager):
        """Test database reset with upgrade failure"""
        with patch.object(migration_manager, 'downgrade_database', return_value=True), \
             patch.object(migration_manager, 'upgrade_database', return_value=False):
            
            result = migration_manager.reset_database()
            
            assert result is False


class TestMigrationIntegration:
    """Integration tests for migration system"""
    
    @pytest.fixture
    def temp_db_url(self):
        """Create temporary SQLite database for integration testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"
            yield db_url
            # Cleanup
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
    
    def test_migration_creates_all_tables(self, temp_db_url):
        """Test that migration creates all expected tables"""
        # Patch UUID for SQLite compatibility
        from tests.test_utils import patch_uuid_for_sqlite
        patch_uuid_for_sqlite()
        
        # Create engine and run migration
        engine = create_engine(temp_db_url)
        
        # Create all tables using SQLAlchemy (simulating migration)
        Base.metadata.create_all(bind=engine)
        
        # Check that all expected tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            "users",
            "email_verification_tokens",
            "password_reset_tokens",
            "style_profiles",
            "quiz_questions",
            "clothing_categories",
            "clothing_items",
            "outfit_recommendations",
            "outfit_clothing_items",
            "recommendation_feedback"
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table {table} not found in database"
    
    def test_migration_creates_correct_columns(self, temp_db_url):
        """Test that migration creates tables with correct columns"""
        # Patch UUID for SQLite compatibility
        from tests.test_utils import patch_uuid_for_sqlite
        patch_uuid_for_sqlite()
        
        engine = create_engine(temp_db_url)
        Base.metadata.create_all(bind=engine)
        
        inspector = inspect(engine)
        
        # Check users table columns
        users_columns = {col["name"]: col for col in inspector.get_columns("users")}
        expected_user_columns = ["id", "email", "password_hash", "first_name", "last_name", "is_verified", "is_active", "created_at", "updated_at"]
        
        for col_name in expected_user_columns:
            assert col_name in users_columns, f"Column {col_name} not found in users table"
        
        # Check clothing_items table columns
        items_columns = {col["name"]: col for col in inspector.get_columns("clothing_items")}
        expected_item_columns = ["id", "user_id", "filename", "original_filename", "image_url", "category", "color", "brand", "size"]
        
        for col_name in expected_item_columns:
            assert col_name in items_columns, f"Column {col_name} not found in clothing_items table"
    
    def test_migration_creates_foreign_keys(self, temp_db_url):
        """Test that migration creates proper foreign key relationships"""
        # Patch UUID for SQLite compatibility
        from tests.test_utils import patch_uuid_for_sqlite
        patch_uuid_for_sqlite()
        
        engine = create_engine(temp_db_url)
        Base.metadata.create_all(bind=engine)
        
        inspector = inspect(engine)
        
        # Check foreign keys in clothing_items table
        clothing_items_fks = inspector.get_foreign_keys("clothing_items")
        fk_tables = [fk["referred_table"] for fk in clothing_items_fks]
        
        assert "users" in fk_tables, "Foreign key to users table not found in clothing_items"
        
        # Check foreign keys in style_profiles table
        style_profiles_fks = inspector.get_foreign_keys("style_profiles")
        fk_tables = [fk["referred_table"] for fk in style_profiles_fks]
        
        assert "users" in fk_tables, "Foreign key to users table not found in style_profiles"
    
    def test_migration_creates_indexes(self, temp_db_url):
        """Test that migration creates proper indexes"""
        # Patch UUID for SQLite compatibility
        from tests.test_utils import patch_uuid_for_sqlite
        patch_uuid_for_sqlite()
        
        engine = create_engine(temp_db_url)
        Base.metadata.create_all(bind=engine)
        
        inspector = inspect(engine)
        
        # Check indexes on users table
        users_indexes = inspector.get_indexes("users")
        index_columns = [idx["column_names"] for idx in users_indexes]
        
        # Should have index on email
        assert any("email" in cols for cols in index_columns), "Index on email column not found"
        
        # Check indexes on clothing_items table
        items_indexes = inspector.get_indexes("clothing_items")
        index_columns = [idx["column_names"] for idx in items_indexes]
        
        # Should have index on user_id and category
        assert any("user_id" in cols for cols in index_columns), "Index on user_id column not found"
        assert any("category" in cols for cols in index_columns), "Index on category column not found"


class TestMigrationRollback:
    """Test migration rollback functionality"""
    
    @pytest.fixture
    def temp_db_url(self):
        """Create temporary SQLite database for rollback testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"
            yield db_url
            # Cleanup
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
    
    def test_rollback_removes_tables(self, temp_db_url):
        """Test that rollback properly removes tables"""
        # Patch UUID for SQLite compatibility
        from tests.test_utils import patch_uuid_for_sqlite
        patch_uuid_for_sqlite()
        
        engine = create_engine(temp_db_url)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Verify tables exist
        inspector = inspect(engine)
        tables_before = inspector.get_table_names()
        assert len(tables_before) > 0, "No tables created"
        
        # Drop tables (simulating rollback)
        Base.metadata.drop_all(bind=engine)
        
        # Verify tables are removed
        inspector = inspect(engine)
        tables_after = inspector.get_table_names()
        assert len(tables_after) == 0, "Tables not properly removed during rollback"
    
    def test_rollback_handles_foreign_key_constraints(self, temp_db_url):
        """Test that rollback properly handles foreign key constraints"""
        # Patch UUID for SQLite compatibility
        from tests.test_utils import patch_uuid_for_sqlite
        patch_uuid_for_sqlite()
        
        engine = create_engine(temp_db_url)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Insert test data to create foreign key relationships
        with engine.connect() as conn:
            # Insert user
            conn.execute(text("""
                INSERT INTO users (id, email, password_hash, first_name, last_name, is_verified, is_active)
                VALUES ('550e8400-e29b-41d4-a716-446655440000', 'test@example.com', 'hash', 'Test', 'User', true, true)
            """))
            
            # Insert clothing item with foreign key to user
            conn.execute(text("""
                INSERT INTO clothing_items (id, user_id, filename, original_filename, image_url, category, times_recommended)
                VALUES ('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440000', 'test.jpg', 'test.jpg', '/test.jpg', 'shirt', 0)
            """))
            
            conn.commit()
        
        # Verify data exists
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM clothing_items")).scalar()
            assert result == 1, "Test data not inserted"
        
        # Drop tables (simulating rollback) - should handle foreign keys properly
        Base.metadata.drop_all(bind=engine)
        
        # Verify all tables are removed
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert len(tables) == 0, "Tables not properly removed with foreign key constraints"


@patch('app.core.migration_utils.MigrationManager')
def test_run_migration_tests_success(mock_manager_class):
    """Test successful migration test run"""
    # Setup mock manager
    mock_manager = MagicMock()
    mock_manager.check_migration_status.return_value = {"error": None}
    mock_manager.check_database_schema.return_value = {"error": None}
    mock_manager.get_available_revisions.return_value = ["rev1", "rev2"]
    mock_manager.validate_migration.return_value = {
        "upgrade_success": True,
        "downgrade_success": True
    }
    mock_manager_class.return_value = mock_manager
    
    # Test
    results = run_migration_tests()
    
    # Assertions
    assert results["overall_success"] is True
    assert results["status_check"]["error"] is None
    assert results["schema_check"]["error"] is None
    assert "rev1" in results["migration_validation"]
    assert "rev2" in results["migration_validation"]


@patch('app.core.migration_utils.MigrationManager')
def test_run_migration_tests_failure(mock_manager_class):
    """Test migration test run with failures"""
    # Setup mock manager
    mock_manager = MagicMock()
    mock_manager.check_migration_status.return_value = {"error": "Status error"}
    mock_manager.check_database_schema.return_value = {"error": None}
    mock_manager.get_available_revisions.return_value = ["rev1"]
    mock_manager.validate_migration.return_value = {
        "upgrade_success": False,
        "downgrade_success": False
    }
    mock_manager_class.return_value = mock_manager
    
    # Test
    results = run_migration_tests()
    
    # Assertions
    assert results["overall_success"] is False
    assert results["status_check"]["error"] == "Status error"