.PHONY: help install dev-install clean test format lint run-import run-validate run-query

help: ## Show this help message
	@echo "GTFS Dgraph Importer - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

config: ## Show current Dgraph configuration
	uvx run dgraph_config.py

config-example: ## Create example configuration file
	@if [ ! -f config.env ]; then \
		cp config.env.example config.env; \
		echo "✅ Created config.env from example"; \
		echo "📝 Edit config.env with your Dgraph connection details"; \
	else \
		echo "⚠️  config.env already exists"; \
	fi

install: ## Install project dependencies
	uv venv
	uv pip install -e .

dev-install: ## Install project with development dependencies
	uv venv
	uv pip install -e ".[dev]"

clean: ## Remove virtual environment
	uv venv remove

test: ## Run tests
	uv run pytest

format: ## Format code with black
	uv run black .

lint: ## Lint code with flake8
	uv run flake8 .

run-import: ## Run GTFS import script
	uvx run gtfs_import.py

run-validate: ## Run GTFS data validation
	uvx run test_gtfs_data.py

run-query: ## Run sample queries
	uvx run sample_queries.py

start-dgraph: ## Start Dgraph services
	docker-compose up -d

stop-dgraph: ## Stop Dgraph services
	docker-compose down

logs: ## View Dgraph logs
	docker-compose logs -f dgraph

status: ## Check Dgraph status
	@echo "Checking Dgraph health..."
	@curl -s http://localhost:8080/health || echo "Dgraph not responding"
