.PHONY: help install dev-install clean test format lint run-import run-validate run-query

help: ## Show this help message
	@echo "GTFS Neo4j Importer - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

config-neo4j: ## Show current Neo4j configuration
	uvx run neo4j_config.py

config-example: ## Create example configuration file
	@if [ ! -f config.env ]; then \
		cp config.env.neo4j.example config.env; \
		echo "✅ Created config.env from example"; \
		echo "📝 Edit config.env with your Neo4j connection details"; \
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

run-import-neo4j: ## Run GTFS import script for Neo4j
	uvx run gtfs_import_neo4j.py

run-validate: ## Run GTFS data validation
	uvx run test_gtfs_data.py

run-query-neo4j: ## Run sample queries for Neo4j
	uvx run sample_queries_neo4j.py

start-neo4j: ## Start Neo4j services
	docker-compose -f docker-compose-neo4j.yml up -d

stop-neo4j: ## Stop Neo4j services
	docker-compose -f docker-compose-neo4j.yml down

logs-neo4j: ## View Neo4j logs
	docker-compose -f docker-compose-neo4j.yml logs -f

status-neo4j: ## Check Neo4j status
	@echo "Checking Neo4j health..."
	@curl -s http://localhost:7474/db/neo4j/tx/commit || echo "Neo4j not responding"
