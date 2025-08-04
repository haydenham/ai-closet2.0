# Database Migration System

This document describes the database migration system implemented for the Fashion AI platform.

## Overview

The migration system provides comprehensive tools for managing database schema changes, including:

- **Initial migration scripts** for all database tables
- **Migration testing and validation** utilities
- **Rollback procedures** for safe schema changes
- **CLI tools** for migration management
- **Integration tests** for migration reliability

## Files and Structure

```
backend/
├── alembic/
│   ├── versions/
│   │   └── 001_initial_setup.py      # Initial migration script
│   ├── env.py                        # Alembic environment configuration
│   └── script.py.mako               # Migration template
├── alembic.ini                       # Alembic configuration
├── app/core/
│   └── migration_utils.py            # Migration management utilities
├── scripts/
│   └── manage_migrations.py          # CLI migration management tool
├── tests/
│   └── test_migrations.py            # Migration integration tests
└── docs/
    └── migrations.md                 # This documentation
```

## Database Schema

The initial migration creates the following tables:

### Core Tables
- **users** - User accounts and authentication
- **email_verification_tokens** - Email verification tokens
- **password_reset_tokens** - Password reset tokens

### Style and Profile Tables
- **style_profiles** - User style preferences and AI model assignments
- **quiz_questions** - Style assessment quiz questions

### Closet Management Tables
- **clothing_categories** - Hierarchical clothing categories
- **clothing_items** - User's clothing items with embeddings

### Recommendation Tables
- **outfit_recommendations** - AI-generated outfit suggestions
- **outfit_clothing_items** - Association table for recommendations and items
- **recommendation_feedback** - User feedback on recommendations

## Usage

### Using Make Commands

The easiest way to manage migrations is through the provided Makefile commands:

```bash
# Show migration status
make migrate-status

# Run migrations (upgrade to latest)
make migrate

# Create new migration
make migration msg="Add new feature"

# Test migrations
make migrate-test

# Validate specific migration
make migrate-validate rev=abc123

# Show database schema
make migrate-schema

# Reset database (careful!)
make migrate-reset

# Downgrade to specific revision
make migrate-down rev=abc123

# Backup schema
make migrate-backup file=backup.sql
```

### Using CLI Script Directly

You can also use the CLI script directly for more advanced options:

```bash
# Show migration status
python scripts/manage_migrations.py status

# Show status in JSON format
python scripts/manage_migrations.py status --json

# Upgrade to latest
python scripts/manage_migrations.py upgrade

# Upgrade to specific revision
python scripts/manage_migrations.py upgrade --revision abc123

# Create new migration with autogenerate
python scripts/manage_migrations.py create --message "Add user preferences"

# Run comprehensive migration tests
python scripts/manage_migrations.py test

# Validate specific migration (tests upgrade/downgrade)
python scripts/manage_migrations.py validate --revision abc123

# Show database schema
python scripts/manage_migrations.py schema

# Reset database (downgrade to base, then upgrade to head)
python scripts/manage_migrations.py reset --force

# Downgrade to specific revision
python scripts/manage_migrations.py downgrade --revision base --force

# Backup database schema (PostgreSQL only)
python scripts/manage_migrations.py backup --output schema_backup.sql
```

### Using Alembic Directly

For advanced users, you can still use Alembic commands directly:

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# Create new migration
alembic revision --autogenerate -m "Add new feature"
```

## Migration Testing

The system includes comprehensive tests for migration reliability:

### Test Categories

1. **Unit Tests** - Test individual migration utility functions
2. **Integration Tests** - Test complete migration workflows
3. **Rollback Tests** - Test migration rollback procedures
4. **Schema Validation** - Verify database schema correctness

### Running Tests

```bash
# Run all migration tests
python -m pytest tests/test_migrations.py -v

# Run specific test categories
python -m pytest tests/test_migrations.py::TestMigrationManager -v
python -m pytest tests/test_migrations.py::TestMigrationIntegration -v
python -m pytest tests/test_migrations.py::TestMigrationRollback -v

# Run tests with coverage
python -m pytest tests/test_migrations.py --cov=app.core.migration_utils
```

## Migration Validation

The system provides built-in validation for migrations:

### Automatic Validation

- **Upgrade Testing** - Verifies migrations can be applied successfully
- **Downgrade Testing** - Verifies migrations can be rolled back safely
- **Schema Consistency** - Checks that schema matches model definitions
- **Foreign Key Integrity** - Validates foreign key relationships

### Manual Validation

```bash
# Validate specific migration
python scripts/manage_migrations.py validate --revision abc123

# Run comprehensive migration test suite
python scripts/manage_migrations.py test
```

## Best Practices

### Creating Migrations

1. **Always review** generated migrations before applying
2. **Test migrations** in development environment first
3. **Use descriptive messages** for migration names
4. **Keep migrations small** and focused on single changes
5. **Backup database** before applying migrations in production

### Migration Safety

1. **Test rollbacks** before deploying to production
2. **Use transactions** for complex migrations
3. **Avoid data loss** operations without explicit confirmation
4. **Monitor migration performance** on large datasets
5. **Have rollback plan** ready for production deployments

### Development Workflow

1. **Make model changes** in SQLAlchemy models
2. **Generate migration** using autogenerate
3. **Review and edit** migration script if needed
4. **Test migration** locally
5. **Validate rollback** procedure
6. **Commit migration** to version control
7. **Apply migration** in staging/production

## Troubleshooting

### Common Issues

**Migration fails with foreign key error:**
```bash
# Check foreign key constraints
python scripts/manage_migrations.py schema
# Fix constraint issues in migration script
```

**Database out of sync:**
```bash
# Check current status
python scripts/manage_migrations.py status
# Reset database if needed (development only)
python scripts/manage_migrations.py reset --force
```

**Migration validation fails:**
```bash
# Run detailed validation
python scripts/manage_migrations.py validate --revision abc123
# Check migration script for issues
```

### Recovery Procedures

**Rollback failed migration:**
```bash
# Downgrade to previous working revision
python scripts/manage_migrations.py downgrade --revision previous_revision --force
```

**Reset development database:**
```bash
# Complete database reset (development only)
python scripts/manage_migrations.py reset --force
```

**Backup before risky operations:**
```bash
# Create schema backup
python scripts/manage_migrations.py backup --output pre_migration_backup.sql
```

## Production Deployment

### Pre-deployment Checklist

- [ ] Migration tested in development
- [ ] Migration tested in staging
- [ ] Rollback procedure tested
- [ ] Database backup created
- [ ] Downtime window planned (if needed)
- [ ] Monitoring alerts configured

### Deployment Steps

1. **Create backup** of production database
2. **Apply migration** using deployment scripts
3. **Verify migration** success
4. **Test application** functionality
5. **Monitor** for issues
6. **Rollback** if problems detected

### Monitoring

- Monitor migration execution time
- Check for lock contention during migration
- Verify application functionality post-migration
- Monitor error logs for migration-related issues

## Configuration

### Environment Variables

The migration system uses the following configuration:

- `DATABASE_URL` - Database connection string
- `ALEMBIC_CONFIG` - Path to alembic.ini (optional)

### Database Support

- **Primary**: PostgreSQL (production)
- **Testing**: SQLite (development/testing)
- **Future**: MySQL/MariaDB support planned

## Contributing

When contributing migration-related changes:

1. **Add tests** for new migration utilities
2. **Update documentation** for new features
3. **Follow naming conventions** for migration files
4. **Test with both PostgreSQL and SQLite**
5. **Validate rollback procedures**

## Support

For migration-related issues:

1. Check this documentation
2. Review migration test failures
3. Use CLI validation tools
4. Check Alembic documentation
5. Consult team for complex issues