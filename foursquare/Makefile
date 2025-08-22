# Makefile for Foursquare Neo4j Import

# Configuration
PYTHON := python3
DATA_DIR := data
CONFIG_FILE := config.env
TEST_CONFIG_FILE := test_config.env
BATCH_SIZE := 1000

# Default target
.PHONY: help
help:
	@echo "Foursquare Neo4j Import Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  setup       - Install dependencies and create config"
	@echo "  test        - Test Neo4j connection"
	@echo "  schema      - Apply Neo4j schema"
	@echo "  import      - Import all data"
	@echo "  queries     - Run sample queries"
	@echo "  clean       - Clean temporary files"
	@echo "  reset       - Reset database (WARNING: deletes all data)"
	@echo ""
	@echo "Testing targets:"
	@echo "  test-setup  - Setup test environment"
	@echo "  test-unit   - Run unit tests only"
	@echo "  test-integration - Run integration tests (requires Neo4j)"
	@echo "  test-all    - Run all tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  generate-test-data - Generate test data fixtures"
	@echo ""
	@echo "Options:"
	@echo "  DATA_DIR    - Data directory (default: data)"
	@echo "  CONFIG_FILE - Config file path (default: config.env)"
	@echo "  TEST_CONFIG_FILE - Test config file (default: test_config.env)"
	@echo "  BATCH_SIZE  - Import batch size (default: 1000)"

.PHONY: setup
setup:
	@echo "Setting up Foursquare Neo4j environment..."
	pip install neo4j pandas python-dotenv
	@if [ ! -f $(CONFIG_FILE) ]; then \
		cp config.env.example $(CONFIG_FILE); \
		echo "Created $(CONFIG_FILE) - please edit with your Neo4j credentials"; \
	else \
		echo "$(CONFIG_FILE) already exists"; \
	fi

# Testing setup and targets
.PHONY: test-setup
test-setup:
	@echo "Setting up test environment..."
	pip install neo4j pandas python-dotenv pytest pytest-mock pytest-cov pytest-timeout
	@if [ ! -f $(TEST_CONFIG_FILE) ]; then \
		cp test_config.env.example $(TEST_CONFIG_FILE); \
		echo "Created $(TEST_CONFIG_FILE) - please edit with your test Neo4j credentials"; \
	else \
		echo "$(TEST_CONFIG_FILE) already exists"; \
	fi

.PHONY: generate-test-data
generate-test-data:
	@echo "Generating test data fixtures..."
	$(PYTHON) tests/fixtures/test_data_generator.py --output-dir tests/fixtures/data

.PHONY: test-unit
test-unit:
	@echo "Running unit tests..."
	$(PYTHON) -m pytest tests/ -m "unit" -v

.PHONY: test-integration
test-integration:
	@echo "Running integration tests..."
	@echo "⚠️  This requires a running Neo4j instance configured for testing"
	RUN_INTEGRATION_TESTS=1 $(PYTHON) -m pytest tests/ -m "integration" -v

.PHONY: test-geospatial
test-geospatial:
	@echo "Running geospatial tests..."
	@echo "⚠️  This requires Neo4j with spatial support"
	RUN_INTEGRATION_TESTS=1 $(PYTHON) -m pytest tests/ -m "geospatial" -v

.PHONY: test-all
test-all: generate-test-data
	@echo "Running all tests..."
	@echo "⚠️  This requires a running Neo4j instance configured for testing"
	RUN_INTEGRATION_TESTS=1 $(PYTHON) -m pytest tests/ -v

.PHONY: test-coverage
test-coverage: generate-test-data
	@echo "Running tests with coverage..."
	RUN_INTEGRATION_TESTS=1 $(PYTHON) -m pytest tests/ --cov=foursquare_import_neo4j --cov=sample_queries_neo4j --cov=routing_queries --cov-report=html --cov-report=term -v

.PHONY: test-quick
test-quick:
	@echo "Running quick unit tests..."
	$(PYTHON) -m pytest tests/test_foursquare_import.py tests/test_data_validation.py -v

.PHONY: test-lint
test-lint:
	@echo "Running code quality checks..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 *.py tests/ --max-line-length=120 --ignore=E501,W503; \
	else \
		echo "flake8 not installed, skipping lint check"; \
	fi

.PHONY: test-clean
test-clean:
	@echo "Cleaning test artifacts..."
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf tests/fixtures/data/*.txt tests/fixtures/data/*.csv
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

.PHONY: test
test:
	@echo "Testing Neo4j connection..."
	$(PYTHON) -c "import sys; sys.path.append('../gtfs'); from neo4j_config import Neo4jConfig; from neo4j import GraphDatabase; config = Neo4jConfig('$(CONFIG_FILE)'); driver = GraphDatabase.driver(config.uri, auth=config.get_auth()); session = driver.session(database=config.database); print('✅ Connection successful') if session.run('RETURN 1').single() else print('❌ Connection failed')"

.PHONY: schema
schema:
	@echo "Applying Neo4j schema..."
	@if command -v cypher-shell >/dev/null 2>&1; then \
		cypher-shell < neo4j_schema.cypher; \
	else \
		echo "cypher-shell not found, schema will be applied during import"; \
	fi

.PHONY: import
import:
	@echo "Importing Foursquare data..."
	$(PYTHON) foursquare_import_neo4j.py --config-file $(CONFIG_FILE) --data-dir $(DATA_DIR) --batch-size $(BATCH_SIZE)

.PHONY: queries
queries:
	@echo "Running sample queries..."
	$(PYTHON) sample_queries_neo4j.py

.PHONY: clean
clean: test-clean
	@echo "Cleaning temporary files..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -f .DS_Store

.PHONY: reset
reset:
	@echo "⚠️  WARNING: This will delete ALL data in the Neo4j database!"
	@read -p "Are you sure? (y/N) " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "Resetting database..."
	$(PYTHON) -c "import sys; sys.path.append('../gtfs'); from neo4j_config import Neo4jConfig; from neo4j import GraphDatabase; config = Neo4jConfig('$(CONFIG_FILE)'); driver = GraphDatabase.driver(config.uri, auth=config.get_auth()); session = driver.session(database=config.database); session.run('MATCH (n) DETACH DELETE n'); print('Database reset complete')"

# Data validation targets
.PHONY: validate-data
validate-data:
	@echo "Validating data files..."
	@if [ ! -f "$(DATA_DIR)/stops.txt" ]; then echo "❌ Missing stops.txt"; exit 1; fi
	@if [ ! -f "$(DATA_DIR)/king_county_places_near_stops.csv" ]; then echo "❌ Missing king_county_places_near_stops.csv"; exit 1; fi
	@echo "✅ Data files found"

.PHONY: validate-config
validate-config:
	@echo "Validating configuration..."
	@if [ ! -f "$(CONFIG_FILE)" ]; then echo "❌ Missing $(CONFIG_FILE)"; exit 1; fi
	$(PYTHON) -c "import sys; sys.path.append('../gtfs'); from neo4j_config import Neo4jConfig; config = Neo4jConfig('$(CONFIG_FILE)'); assert config.validate_connection(), 'Invalid configuration'"
	@echo "✅ Configuration valid"

# Complete workflow
.PHONY: all
all: validate-config validate-data import queries

# Development targets
.PHONY: dev-setup
dev-setup: setup test-setup
	@echo "Installing development dependencies..."
	pip install jupyter matplotlib seaborn flake8 black isort

.PHONY: stats
stats:
	@echo "Database statistics..."
	$(PYTHON) -c "import sys; sys.path.append('../gtfs'); from neo4j_config import Neo4jConfig; from neo4j import GraphDatabase; config = Neo4jConfig('$(CONFIG_FILE)'); driver = GraphDatabase.driver(config.uri, auth=config.get_auth()); session = driver.session(database=config.database); result = session.run('MATCH (n) RETURN labels(n)[0] as type, count(n) as count ORDER BY count DESC'); [print(f'{r[\"type\"]}: {r[\"count\"]:,}') for r in result]"