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

# Run database migrations
migrate:
	alembic upgrade head

# Create new migration
migration:
	alembic revision --autogenerate -m "$(msg)"