#!/usr/bin/env python3
"""
Migration management CLI script

This script provides a command-line interface for managing database migrations,
including running migrations, testing rollbacks, and validating migration integrity.
"""
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.migration_utils import MigrationManager, run_migration_tests
from app.core.config import settings


def print_json(data: Dict[str, Any], indent: int = 2) -> None:
    """Pretty print JSON data"""
    print(json.dumps(data, indent=indent, default=str))


def print_status(status: Dict[str, Any]) -> None:
    """Print migration status in a readable format"""
    print("=== Migration Status ===")
    print(f"Current Revision: {status.get('current_revision', 'None')}")
    print(f"Up to Date: {status.get('is_up_to_date', False)}")
    
    available = status.get('available_revisions', [])
    print(f"Available Revisions: {len(available)}")
    for i, rev in enumerate(available):
        marker = "→" if rev == status.get('current_revision') else " "
        print(f"  {marker} {rev}")
    
    pending = status.get('pending_migrations', [])
    if pending:
        print(f"Pending Migrations: {len(pending)}")
        for rev in pending:
            print(f"  • {rev}")
    else:
        print("No pending migrations")


def print_schema_info(schema: Dict[str, Any]) -> None:
    """Print database schema information"""
    if "error" in schema:
        print(f"Error checking schema: {schema['error']}")
        return
    
    print("=== Database Schema ===")
    tables = schema.get('tables', [])
    print(f"Total Tables: {len(tables)}")
    
    for table in tables:
        print(f"\nTable: {table}")
        details = schema.get('table_details', {}).get(table, {})
        
        columns = details.get('columns', [])
        print(f"  Columns ({len(columns)}):")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"    {col['name']}: {col['type']} {nullable}")
        
        indexes = details.get('indexes', [])
        if indexes:
            print(f"  Indexes ({len(indexes)}):")
            for idx in indexes:
                unique = "UNIQUE" if idx['unique'] else ""
                print(f"    {idx['name']}: {', '.join(idx['columns'])} {unique}")
        
        fks = details.get('foreign_keys', [])
        if fks:
            print(f"  Foreign Keys ({len(fks)}):")
            for fk in fks:
                print(f"    {fk['name']}: {', '.join(fk['constrained_columns'])} → {fk['referred_table']}.{', '.join(fk['referred_columns'])}")


def print_test_results(results: Dict[str, Any]) -> None:
    """Print migration test results"""
    print("=== Migration Test Results ===")
    print(f"Overall Success: {results.get('overall_success', False)}")
    
    # Status check results
    status_check = results.get('status_check', {})
    if status_check.get('error'):
        print(f"Status Check Error: {status_check['error']}")
    else:
        print("Status Check: ✓ PASSED")
    
    # Schema check results
    schema_check = results.get('schema_check', {})
    if schema_check.get('error'):
        print(f"Schema Check Error: {schema_check['error']}")
    else:
        print("Schema Check: ✓ PASSED")
    
    # Migration validation results
    validations = results.get('migration_validation', {})
    print(f"\nMigration Validations ({len(validations)}):")
    
    for revision, validation in validations.items():
        upgrade_status = "✓" if validation.get('upgrade_success') else "✗"
        downgrade_status = "✓" if validation.get('downgrade_success') else "✗"
        
        print(f"  {revision}:")
        print(f"    Upgrade: {upgrade_status}")
        print(f"    Downgrade: {downgrade_status}")
        
        errors = validation.get('errors', [])
        if errors:
            print(f"    Errors:")
            for error in errors:
                print(f"      • {error}")


def cmd_status(args) -> None:
    """Handle status command"""
    manager = MigrationManager()
    status = manager.check_migration_status()
    
    if args.json:
        print_json(status)
    else:
        print_status(status)


def cmd_upgrade(args) -> None:
    """Handle upgrade command"""
    manager = MigrationManager()
    revision = args.revision or "head"
    
    print(f"Upgrading database to revision: {revision}")
    success = manager.upgrade_database(revision)
    
    if success:
        print("✓ Upgrade completed successfully")
        if not args.quiet:
            # Show updated status
            status = manager.check_migration_status()
            print_status(status)
    else:
        print("✗ Upgrade failed")
        sys.exit(1)


def cmd_downgrade(args) -> None:
    """Handle downgrade command"""
    if not args.revision:
        print("Error: --revision is required for downgrade")
        sys.exit(1)
    
    manager = MigrationManager()
    
    # Confirm downgrade
    if not args.force:
        current = manager.get_current_revision()
        print(f"WARNING: This will downgrade from {current} to {args.revision}")
        confirm = input("Are you sure? (y/N): ")
        if confirm.lower() != 'y':
            print("Downgrade cancelled")
            return
    
    print(f"Downgrading database to revision: {args.revision}")
    success = manager.downgrade_database(args.revision)
    
    if success:
        print("✓ Downgrade completed successfully")
        if not args.quiet:
            # Show updated status
            status = manager.check_migration_status()
            print_status(status)
    else:
        print("✗ Downgrade failed")
        sys.exit(1)


def cmd_create(args) -> None:
    """Handle create migration command"""
    if not args.message:
        print("Error: --message is required for creating migrations")
        sys.exit(1)
    
    manager = MigrationManager()
    
    print(f"Creating migration: {args.message}")
    success = manager.create_migration(args.message, autogenerate=args.autogenerate)
    
    if success:
        print("✓ Migration created successfully")
    else:
        print("✗ Migration creation failed")
        sys.exit(1)


def cmd_test(args) -> None:
    """Handle test command"""
    print("Running migration tests...")
    results = run_migration_tests()
    
    if args.json:
        print_json(results)
    else:
        print_test_results(results)
    
    if not results.get('overall_success', False):
        sys.exit(1)


def cmd_validate(args) -> None:
    """Handle validate command"""
    if not args.revision:
        print("Error: --revision is required for validation")
        sys.exit(1)
    
    manager = MigrationManager()
    
    print(f"Validating migration: {args.revision}")
    result = manager.validate_migration(args.revision)
    
    if args.json:
        print_json(result)
    else:
        upgrade_status = "✓" if result.get('upgrade_success') else "✗"
        downgrade_status = "✓" if result.get('downgrade_success') else "✗"
        
        print(f"Revision: {result['revision']}")
        print(f"Upgrade: {upgrade_status}")
        print(f"Downgrade: {downgrade_status}")
        
        errors = result.get('errors', [])
        if errors:
            print("Errors:")
            for error in errors:
                print(f"  • {error}")
        
        if not (result.get('upgrade_success') and result.get('downgrade_success')):
            sys.exit(1)


def cmd_schema(args) -> None:
    """Handle schema command"""
    manager = MigrationManager()
    schema = manager.check_database_schema()
    
    if args.json:
        print_json(schema)
    else:
        print_schema_info(schema)


def cmd_reset(args) -> None:
    """Handle reset command"""
    manager = MigrationManager()
    
    # Confirm reset
    if not args.force:
        print("WARNING: This will reset the entire database (downgrade to base, then upgrade to head)")
        confirm = input("Are you sure? (y/N): ")
        if confirm.lower() != 'y':
            print("Reset cancelled")
            return
    
    print("Resetting database...")
    success = manager.reset_database()
    
    if success:
        print("✓ Database reset completed successfully")
        if not args.quiet:
            # Show updated status
            status = manager.check_migration_status()
            print_status(status)
    else:
        print("✗ Database reset failed")
        sys.exit(1)


def cmd_backup(args) -> None:
    """Handle backup command"""
    if not args.output:
        print("Error: --output is required for backup")
        sys.exit(1)
    
    manager = MigrationManager()
    
    print(f"Creating schema backup: {args.output}")
    success = manager.backup_database_schema(args.output)
    
    if success:
        print("✓ Schema backup created successfully")
    else:
        print("✗ Schema backup failed")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Database migration management tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                    # Show migration status
  %(prog)s upgrade                   # Upgrade to latest
  %(prog)s upgrade --revision abc123 # Upgrade to specific revision
  %(prog)s downgrade --revision base # Downgrade to base
  %(prog)s create --message "Add users table" # Create new migration
  %(prog)s test                      # Run migration tests
  %(prog)s validate --revision abc123 # Validate specific migration
  %(prog)s schema                    # Show database schema
  %(prog)s reset --force             # Reset database
  %(prog)s backup --output schema.sql # Backup schema
        """
    )
    
    # Global options
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress verbose output')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show migration status')
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser('upgrade', help='Upgrade database')
    upgrade_parser.add_argument('--revision', help='Target revision (default: head)')
    
    # Downgrade command
    downgrade_parser = subparsers.add_parser('downgrade', help='Downgrade database')
    downgrade_parser.add_argument('--revision', required=True, help='Target revision')
    downgrade_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # Create migration command
    create_parser = subparsers.add_parser('create', help='Create new migration')
    create_parser.add_argument('--message', '-m', required=True, help='Migration message')
    create_parser.add_argument('--autogenerate', action='store_true', default=True, help='Auto-generate migration')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run migration tests')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate specific migration')
    validate_parser.add_argument('--revision', required=True, help='Revision to validate')
    
    # Schema command
    schema_parser = subparsers.add_parser('schema', help='Show database schema')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset database')
    reset_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup database schema')
    backup_parser.add_argument('--output', '-o', required=True, help='Output file path')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    try:
        command_map = {
            'status': cmd_status,
            'upgrade': cmd_upgrade,
            'downgrade': cmd_downgrade,
            'create': cmd_create,
            'test': cmd_test,
            'validate': cmd_validate,
            'schema': cmd_schema,
            'reset': cmd_reset,
            'backup': cmd_backup,
        }
        
        command_func = command_map.get(args.command)
        if command_func:
            command_func(args)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()