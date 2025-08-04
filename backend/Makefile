.PHONY: install test test-cov lint format clean dev docker-up docker-down

# Install dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
install-dev:
	pip install -r requirements.txt
	pip install black flake8 isort

# Run tests
test:
	pytest

# Run tests with coverage
test-cov:
	pytest --cov=app --cov-report=term-missing --cov-report=html

# Lint code
lint:
	flake8 app tests
	black --check app tests
	isort --check-only app tests

# Format code
format:
	black app tests
	isort app tests

# Clean up generated files
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Run development server
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Docker services
docker-up:
	docker-compose up -d

# Stop Docker services
docker-down:
	docker-compose down

# Database Migration Commands

# Run database migrations
migrate:
	python scripts/manage_migrations.py upgrade

# Create new migration
migration:
	python scripts/manage_migrations.py create --message "$(msg)"

# Show migration status
migrate-status:
	python scripts/manage_migrations.py status

# Test migrations
migrate-test:
	python scripts/manage_migrations.py test

# Validate specific migration
migrate-validate:
	python scripts/manage_migrations.py validate --revision $(rev)

# Show database schema
migrate-schema:
	python scripts/manage_migrations.py schema

# Reset database (downgrade to base, then upgrade to head)
migrate-reset:
	python scripts/manage_migrations.py reset --force

# Downgrade database
migrate-down:
	python scripts/manage_migrations.py downgrade --revision $(rev)

# Backup database schema
migrate-backup:
	python scripts/manage_migrations.py backup --output $(file)

# Legacy Alembic commands (for compatibility)
alembic-migrate:
	alembic upgrade head

alembic-migration:
	alembic revision --autogenerate -m "$(msg)"