.PHONY: install lint format test run clean docker-build docker-run docker-down docker-start docker-stop docker-test

install:
	pip install -e ".[dev]"

lint:
	ruff check src tests
	black --check src tests

format:
	ruff check --fix src tests
	black src tests

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src/data_tables --cov-report=term-missing

run:
	flask --app src.data_tables.app run --debug --port 5000

clean:
	rm -rf __pycache__ .pytest_cache .coverage
	rm -rf src/*.egg-info
	rm -f data_tables.db
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

docker-build:
	docker build -t data-tables-api .

docker-run:
	docker-compose up

docker-down:
	docker-compose down -v

docker-start:
	docker run -d --name data-tables-api -p 5000:5000 data-tables-api

docker-stop:
	docker stop data-tables-api && docker rm data-tables-api

docker-test:
	docker run --rm -v "$$(pwd)/tests:/app/tests" data-tables-api \
		bash -c "pip install pytest pytest-cov -q && pytest tests/ -v"

