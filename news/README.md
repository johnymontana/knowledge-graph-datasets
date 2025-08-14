# News Knowledge Graph

A comprehensive knowledge graph system for news articles using Dgraph, AI embeddings, and vector similarity search. This project converts the original HyperNews project to follow modern Python development practices with uv package management.

## 🚀 Features

- **Knowledge Graph Storage**: Store news articles, entities, and relationships in Dgraph
- **AI-Powered Embeddings**: Generate semantic embeddings using OpenAI, Anthropic, or local Ollama models
- **Vector Similarity Search**: Find similar articles using semantic similarity
- **Multi-Provider AI Support**: Works with OpenAI, Anthropic, or local Ollama models
- **Modern Python Stack**: Uses uv for dependency management and virtual environments
- **Comprehensive Tooling**: Import, validate, query, and search news data
- **Docker Support**: Easy local development with Docker Compose

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   JSON Files    │    │  News Importer  │    │   Dgraph DB     │
│   (NYT Data)    │───▶│  + AI Provider  │───▶│  + Vector Index │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Embeddings     │    │  Vector Search  │
                       │  Generator      │    │  + Query API    │
                       └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- **Python 3.8+**
- **uv package manager** (will be installed automatically)
- **Docker & Docker Compose** (for local development)
- **AI API Keys** (OpenAI, Anthropic, or Ollama for local models)

## 🛠️ Installation

### 1. Clone and Setup

```bash
# Navigate to the news directory
cd news

# Run the setup script
chmod +x setup_uv.sh
./setup_uv.sh
```

### 2. Configure Environment

```bash
# Create configuration file
make config-example

# Edit config.env with your settings
nano config.env
```

### 3. Start Dgraph (Local Development)

```bash
# Start Dgraph services
chmod +x start_dgraph.sh
./start_dgraph.sh

# Or use make
make start-dgraph
```

## ⚙️ Configuration

### Environment Variables

Create a `config.env` file with the following variables:

```bash
# Dgraph Connection
DGRAPH_CONNECTION_STRING=dgraph://localhost:8080

# AI Provider (choose one)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# AI Models
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o-mini

# Import Settings
BATCH_SIZE=100
DATA_DIR=data/articles
EMBEDDING_BATCH_SIZE=50

# Ollama (for local models)
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=nomic-embed-text
```

### Connection String Formats

- **Local Dgraph**: `@dgraph://localhost:8080`
- **Hypermode**: `dgraph://host:port?sslmode=verify-ca&bearertoken=token`

## 📊 Data Import

### 1. Prepare Your Data

Place your NYT JSON files in the `data/articles/` directory. The system supports multiple JSON formats:

- Single article files
- Files with `results` array
- Files with `response.docs` array

### 2. Import Articles

```bash
# Import all articles
make run-import

# Or with custom settings
uvx run news_import.py --data-dir data/articles --batch-size 50
```

### 3. Generate Embeddings

```bash
# Generate embeddings for all articles
make run-embeddings

# Generate embeddings for specific topics
uvx run news_embeddings.py --topic "technology" --limit 1000

# Or with custom batch size
uvx run news_embeddings.py --batch-size 25
```

## 🔍 Querying and Search

### 1. Sample Queries

```bash
# Run all sample queries
make run-query

# Run specific query types
uvx run sample_queries.py --basic
uvx run sample_queries.py --vector-search
```

### 2. Vector Similarity Search

```bash
# Search for similar articles
make run-vector-search query="artificial intelligence and machine learning"

# Or directly
uvx run vector_search.py "climate change and global warming" --limit 5

# Search by topic
uvx run vector_search.py "politics" --topic
```

### 3. Custom Queries

The system supports full DQL queries. Examples:

```dql
# Basic article query
{
  articles(func: type(Article), first: 10) {
    uid
    Article.title
    Article.abstract
    Article.published
  }
}

# Articles with topics
{
  articles(func: type(Article), first: 5) @filter(has(Article.topic)) {
    uid
    Article.title
    Article.topic {
      Topic.name
    }
  }
}

# Vector similarity search
query vector_search($embedding: string, $limit: int) {
  articles(func: similar_to(Article.embedding, $limit, $embedding)) {
    uid
    Article.title
    Article.abstract
    score
  }
}
```

## 🧪 Testing and Validation

### 1. Validate Configuration

```bash
# Run all validation tests
make run-validate

# Test specific components
uvx run test_news_data.py --config-only
uvx run test_news_data.py --ai-only
uvx run test_news_data.py --data-only
```

### 2. Quick System Test

```bash
# Quick validation
make quick-test

# Full demo
make demo
```

## 🐳 Docker Development

### Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f dgraph

# Check status
make status
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Or use make
make stop-dgraph
```

### Service URLs

- **Dgraph Alpha**: http://localhost:8080
- **Dgraph GraphQL**: http://localhost:8000
- **Ratel Admin UI**: http://localhost:8001

## 🔧 Development

### Project Structure

```
news/
├── pyproject.toml          # Project configuration and dependencies
├── config.env.example      # Example environment configuration
├── dgraph_config.py        # Dgraph connection management
├── ai_provider.py          # AI provider abstraction layer
├── news_import.py          # Main import script
├── news_embeddings.py      # Embeddings generation
├── vector_search.py        # Vector similarity search
├── sample_queries.py       # Example queries
├── test_news_data.py       # Validation and testing
├── schema.dql              # Dgraph schema definition
├── docker-compose.yml      # Docker services configuration
├── setup_uv.sh            # Setup script
├── start_dgraph.sh        # Dgraph startup script
├── Makefile               # Development commands
└── README_NEWS_IMPORT.md  # This file
```

### Available Commands

```bash
# Show all available commands
make help

# Development
make install              # Install dependencies
make dev-install          # Install with dev dependencies
make clean                # Remove virtual environment
make format               # Format code with black
make lint                 # Lint code with flake8

# Data operations
make run-import           # Import news data
make run-embeddings       # Generate embeddings
make run-query            # Run sample queries
make run-validate         # Validate system

# Docker operations
make start-dgraph         # Start Dgraph services
make stop-dgraph          # Stop Dgraph services
make logs                 # View service logs
make status               # Check service status

# Utility
make config               # Show current configuration
make config-example       # Create example config
make setup                # Complete setup
make quick-test           # Quick system test
make demo                 # Run system demo
```

### Adding New AI Providers

The system uses a provider abstraction pattern. To add a new AI provider:

1. Create a new class implementing the `AIProvider` interface
2. Add the provider to the `get_ai_provider()` factory function
3. Update the configuration handling

Example:

```python
class NewAIProvider(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def generate_embedding(self, text: str) -> List[float]:
        # Implementation here
        pass
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        # Implementation here
        pass
    
    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        # Implementation here
        pass
```

## 📈 Performance Tuning

### Batch Sizes

- **Import Batch Size**: Controls how many N-Quads are sent to Dgraph at once
- **Embedding Batch Size**: Controls how many texts are processed for embeddings simultaneously

### Memory and Limits

The Docker Compose configuration includes optimized settings:

```yaml
command: dgraph start --alpha --limit "mutations-nquad=1000000; query-edge=1000000; query-var=1000000" --memory_mb 2048
```

### Indexing

The schema includes optimized indexes for:

- **Full-text search**: `@index(fulltext)`
- **Vector similarity**: `@index(hnsw(metric:"euclidean"))`
- **Geospatial queries**: `@index(geo)`
- **Date queries**: `@index(year, month, day, hour)`

## 🚨 Troubleshooting

### Common Issues

1. **Dgraph Connection Failed**
   - Check if Dgraph is running: `make status`
   - Verify connection string in `config.env`
   - Check Docker logs: `make logs`

2. **AI Provider Errors**
   - Verify API keys are set correctly
   - Check API rate limits
   - For Ollama, ensure the service is running locally

3. **Import Failures**
   - Check JSON file format
   - Verify data directory path
   - Check Dgraph schema is loaded

4. **Embedding Generation Issues**
   - Verify AI provider configuration
   - Check text length requirements
   - Monitor API usage and limits

### Debug Mode

Enable verbose logging by setting:

```bash
LOG_LEVEL=DEBUG
```

### Health Checks

```bash
# Check Dgraph health
curl http://localhost:8080/health

# Check Ratel
curl http://localhost:8001

# Test configuration
make config
```

## 🔗 API Reference

### NewsImporter

Main class for importing news articles.

```python
from news_import import NewsImporter

importer = NewsImporter("config.env")
importer.import_articles("data/articles", "output.rdf")
```

### NewsEmbeddingsGenerator

Class for generating and updating embeddings.

```python
from news_embeddings import NewsEmbeddingsGenerator

generator = NewsEmbeddingsGenerator("config.env")
generator.generate_embeddings_for_all(limit=1000)
```

### NewsVectorSearch

Class for vector similarity search.

```python
from vector_search import NewsVectorSearch

searcher = NewsVectorSearch("config.env")
results = searcher.search("artificial intelligence", limit=10)
```

### AI Provider

Unified interface for AI operations.

```python
from ai_provider import get_ai_provider

provider = get_ai_provider("openai")  # or "anthropic", "ollama", "auto"
embedding = provider.generate_embedding("text")
```

## 📚 Additional Resources

- [Dgraph Documentation](https://dgraph.io/docs/)
- [DQL Query Language](https://dgraph.io/docs/query-language/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Ollama Documentation](https://ollama.ai/docs)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of the knowledge-graph-datasets repository. Please refer to the main repository license.

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section above
2. Review the logs: `make logs`
3. Run validation: `make run-validate`
4. Check configuration: `make config`

---

**Happy knowledge graphing! 🚀📰**
