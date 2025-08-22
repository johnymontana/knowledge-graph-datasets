# News Knowledge Graph

A comprehensive knowledge graph system for news articles using Neo4j, AI embeddings, and vector similarity search. This project converts the original HyperNews project to follow modern Python development practices with uv package management.

## 🚀 Features

- **Knowledge Graph Storage**: Store news articles, entities, and relationships in Neo4j
- **AI-Powered Embeddings**: Generate semantic embeddings using OpenAI, Anthropic, or local Ollama models
- **Vector Similarity Search**: Find similar articles using semantic similarity with Neo4j vector indexes
- **Multi-Provider AI Support**: Works with OpenAI, Anthropic, or local Ollama models
- **Modern Python Stack**: Uses uv for dependency management and virtual environments
- **Comprehensive Tooling**: Import, validate, query, and search news data
- **Docker Support**: Easy local development with Docker Compose
- **Geospatial Queries**: Support for location-based article queries
- **Temporal Analysis**: Time-based article analysis and filtering

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   JSON Files    │    │  News Importer  │    │    Neo4j DB     │
│   (NYT Data)    │───▶│  + AI Provider  │───▶│  + Vector Index │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Embeddings     │    │  Vector Search  │
                       │  Generator      │    │  + Cypher API   │
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

### 3. Start Neo4j (Local Development)

```bash
# Start Neo4j services
chmod +x start_neo4j.sh
./start_neo4j.sh

# Or use Docker Compose directly
docker-compose up -d
```

## ⚙️ Configuration

### Environment Variables

Create a `config.env` file with the following variables:

```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

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

- **Local Neo4j**: `bolt://localhost:7687`
- **Neo4j Aura**: `neo4j://your-instance.databases.neo4j.io`
- **Neo4j Enterprise**: `bolt://host:7687` or `neo4j://host:7687`

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
uv run news_import_neo4j.py --data-dir data/articles --limit 1000
```

### 3. Generate Embeddings

```bash
# Generate embeddings for all articles
make run-embeddings

# Generate embeddings for specific topics
uv run news_embeddings_neo4j.py --topic "technology" --limit 1000

# Or with custom batch size
uv run news_embeddings_neo4j.py --batch-size 25
```

## 🔍 Querying and Search

### 1. Sample Queries

```bash
# Run all sample queries
make run-query

# Run specific query types
uv run sample_queries_neo4j.py --basic
uv run sample_queries_neo4j.py --vector-search
uv run sample_queries_neo4j.py --geospatial
```

### 2. Vector Similarity Search

```bash
# Search for similar articles
make run-vector-search query="artificial intelligence and machine learning"

# Or directly
uv run vector_search_neo4j.py "climate change and global warming" --limit 5

# Search by topic
uv run vector_search_neo4j.py "politics" --topic
```

### 3. Custom Cypher Queries

The system supports full Cypher queries. Examples:

```cypher
// Basic article query
MATCH (a:Article) 
RETURN a.uri, a.title, a.abstract, a.published 
LIMIT 10

// Articles with topics
MATCH (a:Article)-[:HAS_TOPIC]->(t:Topic)
RETURN a.title, collect(t.name) as topics 
LIMIT 5

// Vector similarity search
CALL db.index.vector.queryNodes('article_embeddings', 10, $queryVector)
YIELD node, score
RETURN node.title, node.abstract, score
ORDER BY score DESC
```

### 4. Geospatial Queries

```cypher
// Articles near a specific location
MATCH (a:Article)-[:LOCATED_IN]->(g:Geo)
WHERE g.location IS NOT NULL
WITH a, g, distance(g.location, point({latitude: 40.7128, longitude: -74.0060})) as dist
WHERE dist < 100000  // 100km in meters
RETURN a.title, g.name, round(dist/1000) as distance_km
ORDER BY dist
```

## 🧪 Testing and Validation

### 1. Validate Configuration

```bash
# Run all validation tests
make run-validate

# Test specific components
uv run test_news_data_neo4j.py --config-only
uv run test_news_data_neo4j.py --ai-only
uv run test_news_data_neo4j.py --data-only
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
docker-compose logs -f neo4j

# Check status
make status
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Or use make
make stop-neo4j
```

### Service URLs

- **Neo4j Browser**: http://localhost:7474
- **Neo4j Bolt Protocol**: bolt://localhost:7687

## 🔧 Development

### Project Structure

```
news/
├── pyproject.toml              # Project configuration and dependencies
├── config.env.example          # Example environment configuration
├── neo4j_config.py             # Neo4j connection management
├── ai_provider.py              # AI provider abstraction layer
├── news_import_neo4j.py        # Main import script for Neo4j
├── news_embeddings_neo4j.py    # Embeddings generation for Neo4j
├── vector_search_neo4j.py      # Vector similarity search for Neo4j
├── sample_queries_neo4j.py     # Example Cypher queries
├── test_news_data_neo4j.py     # Validation and testing for Neo4j
├── schema.cypher               # Neo4j schema definition (Cypher)
├── docker-compose.yml          # Docker services configuration
├── setup_uv.sh                # Setup script
├── start_neo4j.sh             # Neo4j startup script
├── Makefile                    # Development commands
└── README.md                   # This file
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
make run-import           # Import news data to Neo4j
make run-embeddings       # Generate embeddings in Neo4j
make run-query            # Run sample Cypher queries
make run-validate         # Validate system

# Docker operations
make start-neo4j          # Start Neo4j services
make stop-neo4j           # Stop Neo4j services
make logs                 # View service logs
make status               # Check service status

# Utility
make config               # Show current configuration
make config-example       # Create example config
make setup                # Complete setup
make quick-test           # Quick system test
make demo                 # Run system demo
```

### Graph Schema

The Neo4j graph uses the following structure:

**Node Labels:**
- `Article`: News articles with properties like title, abstract, published date
- `Topic`: Article topics/themes
- `Organization`: Organizations mentioned in articles
- `Person`: People mentioned in articles
- `Author`: Article authors
- `Geo`: Geographic locations with optional point geometry
- `Image`: Article images

**Relationships:**
- `HAS_TOPIC`: Article to Topic
- `MENTIONS_ORGANIZATION`: Article to Organization
- `MENTIONS_PERSON`: Article to Person
- `WRITTEN_BY`: Article to Author
- `LOCATED_IN`: Article to Geo
- `HAS_IMAGE`: Article to Image

## 📈 Performance Tuning

### Neo4j Configuration

The Docker Compose configuration includes optimized settings:

```yaml
environment:
  - NEO4J_dbms_memory_heap_initial__size=1G
  - NEO4J_dbms_memory_heap_max__size=2G
  - NEO4J_dbms_memory_pagecache_size=1G
```

### Indexing

The schema includes optimized indexes for:

- **Fulltext search**: `CREATE FULLTEXT INDEX article_text FOR (a:Article) ON EACH [a.title, a.abstract]`
- **Vector similarity**: `CREATE VECTOR INDEX article_embeddings FOR (a:Article) ON (a.embedding)`
- **Property indexes**: For efficient lookups on common properties
- **Constraints**: To ensure data integrity

### Vector Search Performance

- Use appropriate vector dimensions (1536 for OpenAI embeddings)
- Choose the right similarity function (cosine, euclidean, or dot product)
- Consider the trade-off between search quality and performance

## 🚨 Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   - Check if Neo4j is running: `make status`
   - Verify connection settings in `config.env`
   - Check Docker logs: `make logs`

2. **AI Provider Errors**
   - Verify API keys are set correctly
   - Check API rate limits
   - For Ollama, ensure the service is running locally

3. **Import Failures**
   - Check JSON file format
   - Verify data directory path
   - Check Neo4j is accessible and has sufficient memory

4. **Vector Search Issues**
   - Ensure vector index is created: `SHOW INDEXES`
   - Verify articles have embeddings: `MATCH (a:Article) WHERE a.embedding IS NOT NULL RETURN count(a)`
   - Check vector dimensions match your embedding model

### Debug Mode

Enable verbose logging by setting:

```bash
LOG_LEVEL=DEBUG
```

### Health Checks

```bash
# Check Neo4j health
curl http://localhost:7474

# Test connection with Cypher
echo "RETURN 1 as test" | cypher-shell -u neo4j -p password

# Test configuration
make config
```

## 🔗 API Reference

### NewsImporterNeo4j

Main class for importing news articles to Neo4j.

```python
from news_import_neo4j import NewsImporterNeo4j

importer = NewsImporterNeo4j("config.env")
importer.import_articles("data/articles", limit=1000)
```

### NewsEmbeddingsGeneratorNeo4j

Class for generating and updating embeddings in Neo4j.

```python
from news_embeddings_neo4j import NewsEmbeddingsGeneratorNeo4j

generator = NewsEmbeddingsGeneratorNeo4j("config.env")
generator.generate_embeddings_for_all(limit=1000)
```

### NewsVectorSearchNeo4j

Class for vector similarity search in Neo4j.

```python
from vector_search_neo4j import NewsVectorSearchNeo4j

searcher = NewsVectorSearchNeo4j("config.env")
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

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
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

**Happy knowledge graphing with Neo4j! 🚀📰**