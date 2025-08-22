.PHONY: help install dev-install clean test format lint run-import run-validate run-query

help: ## Show this help message
	@echo "OSM Neo4j Importer - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

config: ## Show current Neo4j configuration
	uvx run neo4j_config.py

config-example: ## Create example configuration file
	@if [ ! -f config.env ]; then \
		cp config.env.example config.env; \
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

run-import: ## Run OSM import script
	uvx run osm_import.py

run-full-import: ## Run full OSM import script
	uv run osm_import_enhanced.py

run-validate: ## Run OSM data validation
	uvx run test_osm_data.py

run-query: ## Run sample queries
	uvx run sample_queries.py

start-neo4j: ## Start Neo4j services
	docker-compose up -d

stop-neo4j: ## Stop Neo4j services
	docker-compose down

logs: ## View Neo4j logs
	docker-compose logs -f neo4j

status: ## Check Neo4j status
	@echo "Checking Neo4j health..."
	@curl -s http://localhost:7474/browser/ || echo "Neo4j not responding"
