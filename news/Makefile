.PHONY: help install dev-install clean test format lint run-import run-import-optimized run-import-fast run-embeddings run-query run-vector-search run-validate run-geocode run-geocode-batch check-geo-status check-ollama geocode-workflow geocode-setup

help: ## Show this help message
	@echo "News Knowledge Graph (Neo4j) - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

config: ## Show current Neo4j configuration
	@echo "📋 Current Neo4j Configuration:"
	@echo "NEO4J_URI: $(or $(NEO4J_URI), not set)"
	@echo "NEO4J_USERNAME: $(or $(NEO4J_USERNAME), not set)"
	@echo "NEO4J_DATABASE: $(or $(NEO4J_DATABASE), not set)"

config-example: ## Create example configuration file
	@if [ ! -f config.env ]; then \
		cp config.env.example config.env; \
		echo "✅ Created config.env from example"; \
		echo "📝 Edit config.env with your Neo4j connection details and AI API keys"; \
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

run-import: ## Run news import script for Neo4j
	uv run news_import_neo4j.py

run-import-optimized: ## Run optimized news import script for Neo4j (faster)
	uv run news_import_neo4j_optimized.py --skip-geocoding --skip-embeddings

run-import-fast: ## Run ultra-fast news import (no AI features)
	uv run news_import_neo4j_optimized.py --skip-geocoding --skip-embeddings --limit 100

run-embeddings: ## Run news embeddings generation for Neo4j
	uv run news_embeddings_neo4j.py

run-query: ## Run sample Cypher queries
	uv run sample_queries_neo4j.py

run-vector-search: ## Run vector similarity search (requires query argument)
	@if [ -z "$(query)" ]; then \
		echo "❌ Please provide a query: make run-vector-search query='your search query'"; \
		exit 1; \
	fi
	uv run vector_search_neo4j.py "$(query)"

run-validate: ## Run news data validation for Neo4j
	uv run test_news_data_neo4j.py

run-geocode: ## Geocode Geo nodes without location property
	@echo "🌍 Geocoding Geo nodes without location property..."
	uv run --env-file config.env geocode_geo_nodes.py

run-geocode-batch: ## Geocode Geo nodes with custom batch size and delay
	@if [ -z "$(batch)" ] || [ -z "$(delay)" ]; then \
		echo "❌ Please provide batch size and delay: make run-geocode-batch batch=5 delay=2.0"; \
		exit 1; \
	fi
	@echo "🌍 Geocoding Geo nodes with batch size $(batch) and delay $(delay)s..."
	uv run --env-file config.env geocode_geo_nodes.py $(batch) $(delay)

check-ollama: ## Check if Ollama is running and accessible
	@echo "🤖 Checking Ollama status..."
	@curl -s http://localhost:11434/api/tags > /dev/null 2>&1 && echo "✅ Ollama is running" || echo "❌ Ollama is not running or not accessible"

check-geo-status: ## Check status of Geo nodes (with/without location)
	@echo "📊 Checking Geo nodes status..."
	uv run --env-file config.env check_geo_status.py

geocode-workflow: ## Complete geocoding workflow: check status, geocode, then check again
	@echo "🔄 Starting complete geocoding workflow..."
	@echo ""
	@echo "📊 Step 1: Checking initial status..."
	@make check-geo-status
	@echo ""
	@echo "🌍 Step 2: Running geocoding..."
	@make run-geocode
	@echo ""
	@echo "📊 Step 3: Checking final status..."
	@make check-geo-status
	@echo ""
	@echo "✅ Geocoding workflow complete!"

geocode-setup: ## Check prerequisites for geocoding (Neo4j + Ollama)
	@echo "🔧 Checking geocoding prerequisites..."
	@echo ""
	@echo "📊 Checking Neo4j status..."
	@make status
	@echo ""
	@echo "🤖 Checking Ollama status..."
	@make check-ollama
	@echo ""
	@echo "🌍 Checking Geo nodes status..."
	@make check-geo-status
	@echo ""
	@echo "✅ Prerequisites check complete!"

start-neo4j: ## Start Neo4j services
	docker-compose up -d

stop-neo4j: ## Stop Neo4j services
	docker-compose down

logs: ## View Neo4j logs
	docker-compose logs -f neo4j

status: ## Check Neo4j status
	@echo "Checking Neo4j health..."
	@curl -s http://localhost:7474 > /dev/null 2>&1 && echo "✅ Neo4j Browser accessible" || echo "❌ Neo4j not responding"

setup: ## Run complete setup (install dependencies and create config)
	@echo "🚀 Setting up News Knowledge Graph project..."
	@make install
	@make config-example
	@echo ""
	@echo "✅ Setup complete! Next steps:"
	@echo "   1. Edit config.env with your configuration"
	@echo "   2. Run: make run-validate"
	@echo "   3. Run: make run-import"
	@echo "   4. Run: make run-embeddings"

quick-test: ## Quick test of the system
	@echo "🧪 Running quick system test..."
	@make run-validate
	@echo ""
	@echo "✅ Quick test complete!"

demo: ## Run a demo of the system
	@echo "🎬 Running News Knowledge Graph demo..."
	@echo "1. Testing configuration..."
	@make run-validate
	@echo ""
	@echo "2. Running sample queries..."
	@make run-query
	@echo ""
	@echo "3. Running vector search demo..."
	@make run-vector-search query="artificial intelligence"
	@echo ""
	@echo "🎉 Demo complete!"
