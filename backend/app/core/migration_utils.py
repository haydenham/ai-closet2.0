"""
Migration utilities for database management and testing
"""
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

from app.core.config import settings

logger = logging.getLogger(__name__)


class MigrationManager:
    """Utility class for managing database migrations"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self.alembic_cfg_path = Path(__file__).parent.parent.parent / "alembic.ini"
        
    def get_alembic_config(self) -> Config:
        """Get Alembic configuration"""
        config = Config(str(self.alembic_cfg_path))
        config.set_main_option("sqlalchemy.url", self.database_url)
        return config
    
    def get_current_revision(self) -> Optional[str]:
        """Get current database revision"""
        try:
            engine = create_engine(self.database_url)
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                return context.get_current_revision()
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
    
    def get_available_revisions(self) -> List[str]:
        """Get list of available migration revisions"""
        try:
            config = self.get_alembic_config()
            script = ScriptDirectory.from_config(config)
            revisions = []
            for revision in script.walk_revisions():
                revisions.append(revision.revision)
            return revisions
        except Exception as e:
            logger.error(f"Failed to get available revisions: {e}")
            return []
    
    def check_migration_status(self) -> Dict[str, Any]:
        """Check migration status and return detailed information"""
        try:
            current = self.get_current_revision()
            available = self.get_available_revisions()
            
            status = {
                "current_revision": current,
                "available_revisions": available,
                "is_up_to_date": current == available[0] if available else False,
                "pending_migrations": []
            }
            
            if current and available:
                # Find pending migrations
                current_index = available.index(current) if current in available else -1
                if current_index > 0:
                    status["pending_migrations"] = available[:current_index]
            
            return status
        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return {"error": str(e)}
    
    def upgrade_database(self, revision: str = "head") -> bool:
        """Upgrade database to specified revision"""
        try:
            config = self.get_alembic_config()
            command.upgrade(config, revision)
            logger.info(f"Successfully upgraded database to revision: {revision}")
            return True
        except Exception as e:
            logger.error(f"Failed to upgrade database: {e}")
            return False
    
    def downgrade_database(self, revision: str) -> bool:
        """Downgrade database to specified revision"""
        try:
            config = self.get_alembic_config()
            command.downgrade(config, revision)
            logger.info(f"Successfully downgraded database to revision: {revision}")
            return True
        except Exception as e:
            logger.error(f"Failed to downgrade database: {e}")
            return False
    
    def create_migration(self, message: str, autogenerate: bool = True) -> bool:
        """Create a new migration"""
        try:
            config = self.get_alembic_config()
            if autogenerate:
                command.revision(config, message=message, autogenerate=True)
            else:
                command.revision(config, message=message)
            logger.info(f"Successfully created migration: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            return False
    
    def validate_migration(self, revision: str) -> Dict[str, Any]:
        """Validate a specific migration by testing upgrade and downgrade"""
        validation_result = {
            "revision": revision,
            "upgrade_success": False,
            "downgrade_success": False,
            "errors": []
        }
        
        try:
            # Get current revision before testing
            original_revision = self.get_current_revision()
            
            # Test upgrade
            if self.upgrade_database(revision):
                validation_result["upgrade_success"] = True
                
                # Test downgrade back to original
                if original_revision:
                    if self.downgrade_database(original_revision):
                        validation_result["downgrade_success"] = True
                    else:
                        validation_result["errors"].append("Downgrade failed")
                else:
                    # If no original revision, try to downgrade to base
                    if self.downgrade_database("base"):
                        validation_result["downgrade_success"] = True
                    else:
                        validation_result["errors"].append("Downgrade to base failed")
            else:
                validation_result["errors"].append("Upgrade failed")
                
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def check_database_schema(self) -> Dict[str, Any]:
        """Check current database schema and compare with models"""
        try:
            engine = create_engine(self.database_url)
            inspector = inspect(engine)
            
            schema_info = {
                "tables": inspector.get_table_names(),
                "table_details": {}
            }
            
            for table_name in schema_info["tables"]:
                columns = inspector.get_columns(table_name)
                indexes = inspector.get_indexes(table_name)
                foreign_keys = inspector.get_foreign_keys(table_name)
                
                schema_info["table_details"][table_name] = {
                    "columns": [
                        {
                            "name": col["name"],
                            "type": str(col["type"]),
                            "nullable": col["nullable"],
                            "default": col.get("default")
                        }
                        for col in columns
                    ],
                    "indexes": [
                        {
                            "name": idx["name"],
                            "columns": idx["column_names"],
                            "unique": idx["unique"]
                        }
                        for idx in indexes
                    ],
                    "foreign_keys": [
                        {
                            "name": fk["name"],
                            "constrained_columns": fk["constrained_columns"],
                            "referred_table": fk["referred_table"],
                            "referred_columns": fk["referred_columns"]
                        }
                        for fk in foreign_keys
                    ]
                }
            
            return schema_info
        except Exception as e:
            logger.error(f"Failed to check database schema: {e}")
            return {"error": str(e)}
    
    def reset_database(self) -> bool:
        """Reset database by downgrading to base and upgrading to head"""
        try:
            logger.info("Resetting database...")
            
            # Downgrade to base
            if not self.downgrade_database("base"):
                return False
            
            # Upgrade to head
            if not self.upgrade_database("head"):
                return False
            
            logger.info("Database reset completed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            return False
    
    def backup_database_schema(self, output_file: str) -> bool:
        """Create a backup of the current database schema"""
        try:
            engine = create_engine(self.database_url)
            
            # Use pg_dump for PostgreSQL
            if "postgresql" in self.database_url:
                import subprocess
                from urllib.parse import urlparse
                
                parsed = urlparse(self.database_url)
                cmd = [
                    "pg_dump",
                    "--schema-only",
                    "--no-owner",
                    "--no-privileges",
                    f"--host={parsed.hostname}",
                    f"--port={parsed.port or 5432}",
                    f"--username={parsed.username}",
                    f"--dbname={parsed.path[1:]}",  # Remove leading slash
                    f"--file={output_file}"
                ]
                
                env = {"PGPASSWORD": parsed.password} if parsed.password else {}
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"Schema backup created: {output_file}")
                    return True
                else:
                    logger.error(f"pg_dump failed: {result.stderr}")
                    return False
            else:
                logger.warning("Schema backup only supported for PostgreSQL")
                return False
                
        except Exception as e:
            logger.error(f"Failed to backup schema: {e}")
            return False


def run_migration_tests() -> Dict[str, Any]:
    """Run comprehensive migration tests"""
    manager = MigrationManager()
    test_results = {
        "status_check": None,
        "schema_check": None,
        "migration_validation": {},
        "overall_success": False
    }
    
    try:
        # Check migration status
        test_results["status_check"] = manager.check_migration_status()
        
        # Check database schema
        test_results["schema_check"] = manager.check_database_schema()
        
        # Validate each available migration
        available_revisions = manager.get_available_revisions()
        for revision in available_revisions:
            test_results["migration_validation"][revision] = manager.validate_migration(revision)
        
        # Determine overall success
        all_validations_passed = all(
            result.get("upgrade_success", False) and result.get("downgrade_success", False)
            for result in test_results["migration_validation"].values()
        )
        
        test_results["overall_success"] = (
            test_results["status_check"].get("error") is None and
            test_results["schema_check"].get("error") is None and
            all_validations_passed
        )
        
    except Exception as e:
        test_results["error"] = str(e)
    
    return test_results


if __name__ == "__main__":
    """Command line interface for migration utilities"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration utilities")
    parser.add_argument("command", choices=["status", "upgrade", "downgrade", "test", "reset", "backup"])
    parser.add_argument("--revision", help="Target revision for upgrade/downgrade")
    parser.add_argument("--output", help="Output file for backup")
    
    args = parser.parse_args()
    
    manager = MigrationManager()
    
    if args.command == "status":
        status = manager.check_migration_status()
        print(f"Migration Status: {status}")
    
    elif args.command == "upgrade":
        revision = args.revision or "head"
        success = manager.upgrade_database(revision)
        print(f"Upgrade {'successful' if success else 'failed'}")
    
    elif args.command == "downgrade":
        if not args.revision:
            print("--revision required for downgrade")
            sys.exit(1)
        success = manager.downgrade_database(args.revision)
        print(f"Downgrade {'successful' if success else 'failed'}")
    
    elif args.command == "test":
        results = run_migration_tests()
        print(f"Migration Tests: {results}")
    
    elif args.command == "reset":
        success = manager.reset_database()
        print(f"Database reset {'successful' if success else 'failed'}")
    
    elif args.command == "backup":
        if not args.output:
            print("--output required for backup")
            sys.exit(1)
        success = manager.backup_database_schema(args.output)
        print(f"Schema backup {'successful' if success else 'failed'}")