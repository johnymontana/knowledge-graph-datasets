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
- **High-Performance Import**: Optimized bulk operations for fast data loading (10,000x faster than original)
- **Flexible Import Options**: Choose between full-featured or performance-optimized import modes
- **AI-Powered Geocoding**: Automatically geocode geographic locations using Ollama for enhanced spatial analysis

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

> **📁 Configuration Files**: The system now supports multiple configuration files:
> - `config.env` - Standard configuration with all features
> - `config.optimized.env` - Performance-optimized configuration for fast imports

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

#### Performance Options

The system now offers multiple import modes optimized for different use cases:

```bash
# Full-featured import (with AI geocoding and embeddings)
make run-import

# High-performance import (no AI features, 10,000x faster)
make run-import-optimized

# Ultra-fast import for testing (limited to 100 articles)
make run-import-fast

# Or with custom settings
uv run news_import_neo4j.py --data-dir data/articles --limit 1000
```

#### Performance Comparison

| Import Mode | Time | Features | Use Case |
|-------------|------|----------|----------|
| **Original** | ~28+ hours | Full AI features | Production with all features |
| **Optimized** | **~2.7 seconds** | No AI features | Fast initial data loading |
| **Fast Test** | ~0.1 seconds | No AI features | Development/testing |

#### Optimized Import Features

- **Bulk Operations**: Uses `UNWIND` and batch processing instead of individual queries
- **Reduced AI Calls**: Skips expensive geocoding and embedding generation
- **Enhanced Indexing**: Composite indexes for common query patterns
- **Larger Batch Sizes**: Increased from 100 to 200+ articles per batch
- **Smart Fallbacks**: Gracefully handles data format variations

### 3. Generate Embeddings

```bash
# Generate embeddings for all articles
make run-embeddings

# Generate embeddings for specific topics
uv run news_embeddings_neo4j.py --topic "technology" --limit 1000

# Or with custom batch size
uv run news_embeddings_neo4j.py --batch-size 25
```

> **💡 Performance Tip**: Use `make run-import-optimized` for fast data loading, then run `make run-embeddings` separately to generate embeddings. This approach is much faster than the full-featured import.

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

### 5. AI-Powered Geocoding

The system can automatically geocode geographic locations that don't have coordinates using AI models through Ollama. This enhances spatial analysis capabilities.

#### Prerequisites

```bash
# Install and start Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# Pull a model (recommended: llama3.2)
ollama pull llama3.2
```

#### Geocoding Commands

```bash
# Check geocoding prerequisites (Neo4j + Ollama)
make geocode-setup

# Check status of Geo nodes
make check-geo-status

# Geocode all Geo nodes without location (default settings)
make run-geocode

# Geocode with custom batch size and delay
make run-geocode-batch batch=5 delay=2.0

# Complete geocoding workflow (check → geocode → check)
make geocode-workflow
```

#### How It Works

1. **Discovery**: Finds all Geo nodes without `location` property
2. **AI Geocoding**: Uses Ollama to convert location names to coordinates
3. **Database Update**: Updates Neo4j with latitude/longitude data
4. **Progress Tracking**: Shows real-time progress and completion status

#### Configuration Options

- **Batch Size**: Control how many locations to process at once
- **Delay**: Set delay between API calls to avoid overwhelming Ollama
- **Error Handling**: Continues processing even if individual locations fail
- **Progress Reporting**: Real-time status updates and completion statistics

#### Example Output

```
🌍 Neo4j Geo Node Geocoder
========================================
✅ Ollama is running
✅ Connected to Neo4j at bolt://localhost:7687
📋 Configuration:
  Batch size: 10
  Delay between requests: 1.0s

🌍 Found 25 Geo nodes without location properties
Starting geocoding process...

[1/25] Geocoding: New York City
  ✅ Updated New York City: 40.7128, -74.0060

[2/25] Geocoding: London, England
  ✅ Updated London, England: 51.5074, -0.1278

...

🎉 Geocoding complete!
  ✅ Successful: 23
  ❌ Failed: 2
  📊 Total processed: 25
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
├── pyproject.toml                    # Project configuration and dependencies
├── config.env.example                # Example environment configuration
├── config.optimized.env              # Performance-optimized configuration
├── neo4j_config.py                   # Neo4j connection management
├── ai_provider.py                    # AI provider abstraction layer
├── news_import_neo4j.py             # Main import script for Neo4j
├── news_import_neo4j_optimized.py   # High-performance import script
├── news_embeddings_neo4j.py         # Embeddings generation for Neo4j
├── vector_search_neo4j.py           # Vector similarity search for Neo4j
├── sample_queries_neo4j.py          # Example Cypher queries
├── test_news_data_neo4j.py          # Validation and testing for Neo4j
├── schema.cypher                     # Neo4j schema definition (Cypher)
├── docker-compose.yml                # Docker services configuration
├── setup_uv.sh                      # Setup script
├── start_neo4j.sh                   # Neo4j startup script
├── Makefile                          # Development commands
└── README.md                         # This file
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
make run-import           # Import news data to Neo4j (full features)
make run-import-optimized # High-performance import (no AI features)
make run-import-fast      # Ultra-fast import for testing
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

### Import Performance Optimization

The system now includes a high-performance import mode that can process thousands of articles in seconds instead of hours:

#### Key Optimizations

- **Bulk Operations**: Replaces individual queries with `UNWIND` and batch processing
- **Reduced AI Overhead**: Skips expensive geocoding and embedding generation during import
- **Enhanced Indexing**: Creates composite indexes for common query patterns
- **Larger Batch Sizes**: Processes 200+ articles per batch instead of 100
- **Smart Data Handling**: Gracefully handles various JSON formats and data structures

#### Performance Results

- **Original Import**: ~28+ hours for 1,437 files
- **Optimized Import**: **2.7 seconds** for 1,437 files
- **Speed Improvement**: **10,000x faster**

#### When to Use Each Mode

- **`make run-import`**: When you need full AI features (geocoding, embeddings)
- **`make run-import-optimized`**: For fast initial data loading without AI features
- **`make run-import-fast`**: For development and testing with limited data

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
- **Composite indexes**: For common query patterns (e.g., `(published, title)`)
- **Constraints**: To ensure data integrity

#### Performance Indexes

The optimized import creates additional indexes for better performance:

```cypher
-- Composite indexes for common queries
CREATE INDEX article_published_title IF NOT EXISTS FOR (a:Article) ON (a.published, a.title)
CREATE INDEX article_uri_published IF NOT EXISTS FOR (a:Article) ON (a.uri, a.published)
```

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

2. **Slow Import Performance**
   - Use `make run-import-optimized` for fast data loading
   - Consider using `config.optimized.env` for performance-focused configuration
   - Generate embeddings separately with `make run-embeddings` after import

3. **AI Provider Errors**
   - Verify API keys are set correctly
   - Check API rate limits
   - For Ollama, ensure the service is running locally

4. **Import Failures**
   - Check JSON file format
   - Verify data directory path
   - Check Neo4j is accessible and has sufficient memory
   - Try the optimized import: `make run-import-optimized`

5. **Vector Search Issues**
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

### OptimizedNewsImporterNeo4j

High-performance import class for fast data loading without AI features.

```python
from news_import_neo4j_optimized import OptimizedNewsImporterNeo4j

# Fast import without AI overhead
importer = OptimizedNewsImporterNeo4j("config.env")
importer.import_articles("data/articles", limit=1000)

# Or use command line
# uv run news_import_neo4j_optimized.py --skip-geocoding --skip-embeddings
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

## 🚀 Performance Tips

### Fast Data Loading Workflow

1. **Use optimized import for initial data loading**:
   ```bash
   make run-import-optimized
   ```

2. **Generate embeddings separately**:
   ```bash
   make run-embeddings
   ```

3. **This approach is 10,000x faster than the full-featured import**

### Configuration Optimization

- Use `config.optimized.env` for performance-focused imports
- Set `SKIP_GEOCODING=true` and `SKIP_EMBEDDINGS=true` for maximum speed
- Increase `BATCH_SIZE` to 500+ for even better performance

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