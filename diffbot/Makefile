# Diffbot Knowledge Graph to Neo4j Import - Makefile
# Usage: make <target>

.PHONY: help install setup config-example run-import run-query test clean

# Default target
help:
	@echo "📊 Diffbot Knowledge Graph to Neo4j Import"
	@echo "==========================================="
	@echo ""
	@echo "Available targets:"
	@echo "  install         - Install dependencies using uv"
	@echo "  setup          - Complete setup (install + config)"
	@echo "  config-example - Copy example config file"
	@echo "  start-neo4j    - Start Neo4j using Docker Compose"
	@echo "  stop-neo4j     - Stop Neo4j containers"
	@echo "  run-import     - Run Diffbot data import"
	@echo "  run-query      - Run sample queries"
	@echo "  test           - Run tests"
	@echo "  validate       - Validate data import"
	@echo "  clean          - Clean up generated files"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup && make start-neo4j && make run-import"

# Install dependencies
install:
	@echo "📦 Installing dependencies with uv..."
	uv pip install -e .

# Complete setup
setup: install config-example
	@echo "✅ Setup completed!"
	@echo "Next steps:"
	@echo "1. Edit config.env with your settings"
	@echo "2. Run 'make start-neo4j' to start Neo4j"
	@echo "3. Run 'make run-import' to import data"

# Copy example configuration
config-example:
	@if [ ! -f config.env ]; then \
		echo "📝 Creating config.env from example..."; \
		cp config.env.example config.env; \
		echo "✅ config.env created. Please edit it with your settings."; \
	else \
		echo "⚠️  config.env already exists. Skipping."; \
	fi

# Start Neo4j using Docker Compose
start-neo4j:
	@echo "🚀 Starting Neo4j with Docker Compose..."
	docker-compose up -d
	@echo "⏳ Waiting for Neo4j to be ready..."
	sleep 10
	@echo "✅ Neo4j should be available at http://localhost:7474"

# Stop Neo4j
stop-neo4j:
	@echo "🛑 Stopping Neo4j containers..."
	docker-compose down

# Run the import with default settings
run-import:
	@echo "📥 Running Diffbot import..."
	uv run python diffbot_import_neo4j.py

# Run import with specific query
run-import-query:
	@echo "📥 Running Diffbot import with custom query..."
	@read -p "Enter search query: " query; \
	uv run python diffbot_import_neo4j.py --query "$$query"

# Run import for specific entity types
run-import-organizations:
	@echo "📥 Importing organizations..."
	uv run python diffbot_import_neo4j.py --entity-types Organization

run-import-people:
	@echo "📥 Importing people..."
	uv run python diffbot_import_neo4j.py --entity-types Person

run-import-articles:
	@echo "📥 Importing articles..."
	uv run python diffbot_import_neo4j.py --entity-types Article

# Run sample queries
run-query:
	@echo "🔍 Running sample queries..."
	uv run python sample_queries_neo4j.py

run-query-spatial:
	@echo "🌍 Running spatial queries..."
	uv run python sample_queries_neo4j.py --spatial

run-query-advanced:
	@echo "🧠 Running advanced queries..."
	uv run python sample_queries_neo4j.py --advanced

# Test connection
test-connection:
	@echo "🔧 Testing Neo4j connection..."
	uv run python -c "from neo4j_config import Neo4jConfig; config = Neo4jConfig(); print('✅ Connection OK' if config.validate_connection() else '❌ Connection failed')"

# Validate import
validate:
	@echo "✅ Validating import..."
	uv run python -c "from neo4j_config import Neo4jConfig; from neo4j import GraphDatabase; \
		config = Neo4jConfig(); \
		with config.get_driver().session(database=config.database) as session: \
			result = session.run('MATCH (n:Entity) RETURN count(n) as count'); \
			count = result.single()['count']; \
			print(f'✅ Found {count} entities in database')"

# Run tests (if test files exist)
test:
	@if [ -f "test_diffbot_data.py" ]; then \
		echo "🧪 Running tests..."; \
		uv run python -m pytest test_diffbot_data.py -v; \
	else \
		echo "⚠️  No test files found"; \
	fi

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.log" -delete 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Development targets
dev-format:
	@echo "🎨 Formatting code..."
	uv run black *.py

dev-lint:
	@echo "🔍 Linting code..."
	uv run flake8 *.py

dev: dev-format dev-lint
	@echo "✅ Development checks completed"

# Show configuration
config:
	@echo "⚙️  Current configuration:"
	@if [ -f config.env ]; then \
		echo "📄 config.env contents:"; \
		cat config.env | grep -v "^#" | grep -v "^$$"; \
	else \
		echo "❌ config.env not found. Run 'make config-example' first."; \
	fi

# Docker management
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t diffbot-neo4j-importer .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run --rm -v $(PWD)/config.env:/app/config.env diffbot-neo4j-importer

# Backup and restore (if implemented)
backup:
	@echo "💾 Creating database backup..."
	@echo "⚠️  Backup functionality not implemented yet"

restore:
	@echo "♻️  Restoring database..."
	@echo "⚠️  Restore functionality not implemented yet"