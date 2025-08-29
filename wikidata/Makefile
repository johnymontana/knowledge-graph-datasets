# Wikidata Neo4j Import Makefile
# Provides convenient commands for managing the Wikidata import process

.PHONY: help setup config-example test-connection run-import run-query clean start stop logs

# Default target
help:
	@echo "📊 Wikidata Neo4j Import Commands"
	@echo ""
	@echo "🚀 Setup & Configuration:"
	@echo "  make setup           - Install dependencies and setup environment"
	@echo "  make config-example  - Create example configuration file"
	@echo "  make start           - Start Neo4j database"
	@echo "  make stop            - Stop Neo4j database"
	@echo ""
	@echo "🔍 Testing & Validation:"
	@echo "  make test-connection - Test Neo4j connection"
	@echo "  make validate-data   - Validate imported data"
	@echo ""
	@echo "📥 Import Operations:"
	@echo "  make run-import      - Run Wikidata import (default query)"
	@echo "  make import-scientists - Import scientists from Wikidata"
	@echo "  make import-cities   - Import US cities from Wikidata"
	@echo "  make import-custom   - Run custom SPARQL query"
	@echo ""
	@echo "🔍 Query & Analysis:"
	@echo "  make run-query       - Run sample Neo4j queries"
	@echo "  make schema          - Create Neo4j schema and indexes"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make logs            - Show Neo4j logs"
	@echo "  make clean           - Clean imported data"
	@echo "  make clean-all       - Clean everything including containers"

# Setup and configuration
setup:
	@echo "🚀 Setting up Wikidata import environment..."
	chmod +x setup_uv.sh
	./setup_uv.sh

config-example:
	@if [ ! -f config.env ]; then \
		cp config.env.example config.env; \
		echo "✅ Created config.env from example"; \
		echo "📝 Please edit config.env with your settings"; \
	else \
		echo "⚠️  config.env already exists"; \
	fi

# Database management
start:
	@chmod +x start_neo4j.sh
	@./start_neo4j.sh

stop:
	@echo "🛑 Stopping Neo4j..."
	@docker-compose down

logs:
	@echo "📋 Neo4j logs:"
	@docker-compose logs -f neo4j

# Testing
test-connection:
	@echo "🔌 Testing Neo4j connection..."
	@uv run python -c "from neo4j_config import Neo4jConfig; config = Neo4jConfig(); print('✅ Connection OK' if config.validate_connection() else '❌ Connection failed')"

# Data import
run-import:
	@echo "📥 Running Wikidata import (scientists)..."
	@uv run python wikidata_import_neo4j.py --query-type scientists

import-scientists:
	@echo "📥 Importing scientists from Wikidata..."
	@uv run python wikidata_import_neo4j.py --query-type scientists

import-cities:
	@echo "📥 Importing US cities from Wikidata..."
	@uv run python wikidata_import_neo4j.py --query-type cities

import-custom:
	@echo "📥 Running custom SPARQL query..."
	@echo "💡 Edit the query in wikidata_import_neo4j.py or pass --sparql-file parameter"
	@uv run python wikidata_import_neo4j.py --query-type custom

# Schema and queries
schema:
	@echo "🏗️ Creating Neo4j schema and indexes..."
	@uv run python neo4j_schema.py

run-query:
	@echo "🔍 Running sample queries..."
	@uv run python sample_queries_neo4j.py

validate-data:
	@echo "✅ Validating imported data..."
	@uv run python test_wikidata_data.py

# Cleanup
clean:
	@echo "🧹 Cleaning imported data..."
	@uv run python -c "from neo4j_config import Neo4jConfig; config = Neo4jConfig(); driver = config.get_driver(); driver.execute_query('MATCH (n) DETACH DELETE n', database_=config.get_database()); print('✅ Data cleaned')"

clean-all: clean stop
	@echo "🧹 Removing Docker containers and volumes..."
	@docker-compose down -v
	@docker system prune -f
	@echo "✅ All cleaned up"

# Development
dev-install:
	@echo "🔧 Installing development dependencies..."
	@uv sync --group dev

lint:
	@echo "🔍 Running code linting..."
	@uv run black --check .
	@uv run flake8 .

format:
	@echo "✨ Formatting code..."
	@uv run black .

test:
	@echo "🧪 Running tests..."
	@uv run pytest