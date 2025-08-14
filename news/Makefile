.PHONY: help install dev-install clean test format lint run-import run-embeddings run-query run-vector-search run-validate

help: ## Show this help message
	@echo "News Knowledge Graph - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

config: ## Show current Dgraph configuration
	uvx run dgraph_config.py

config-example: ## Create example configuration file
	@if [ ! -f config.env ]; then \
		cp config.env.example config.env; \
		echo "✅ Created config.env from example"; \
		echo "📝 Edit config.env with your Dgraph connection details and AI API keys"; \
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

run-import: ## Run news import script
	uvx run news_import.py

run-embeddings: ## Run news embeddings generation
	uvx run news_embeddings.py

run-query: ## Run sample queries
	uvx run sample_queries.py

run-vector-search: ## Run vector similarity search (requires query argument)
	@if [ -z "$(query)" ]; then \
		echo "❌ Please provide a query: make run-vector-search query='your search query'"; \
		exit 1; \
	fi
	uvx run vector_search.py "$(query)"

run-validate: ## Run news data validation
	uvx run test_news_data.py

start-dgraph: ## Start Dgraph services
	docker-compose up -d

stop-dgraph: ## Stop Dgraph services
	docker-compose down

logs: ## View Dgraph logs
	docker-compose logs -f dgraph

status: ## Check Dgraph status
	@echo "Checking Dgraph health..."
	@curl -s http://localhost:8080/health || echo "Dgraph not responding"

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
