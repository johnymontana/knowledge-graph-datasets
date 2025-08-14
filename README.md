# Knowledge Graph Datasets

This repository contains various knowledge graph datasets and import tools.

## 🚌 GTFS Transit Data Import

The main project is located in the `gtfs/` directory and provides a complete solution for importing GTFS (General Transit Feed Specification) data into Dgraph.

### Prerequisites

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager
- Dgraph instance (local or remote)
- Configuration file with Dgraph connection details

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Quick Start

```bash
# Navigate to the GTFS project directory
cd gtfs

# Option 1: Use the automated setup script (recommended)
./setup_uv.sh

# Option 2: Manual setup
uv venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows
uv pip install -e .

# Configure Dgraph connection
make config-example
# Edit config.env with your connection details

# Validate GTFS data
uvx run test_gtfs_data.py

# Import data to Dgraph
uvx run gtfs_import.py

# Explore with sample queries
uvx run sample_queries.py
```

### Documentation

- **`gtfs/README_GTFS_Import.md`** - Detailed usage instructions
- **`gtfs/PROJECT_OVERVIEW.md`** - Comprehensive project documentation
- **`gtfs/docker-compose.yml`** - Dgraph setup configuration

### Features

- Complete GTFS data import into Dgraph
- Comprehensive transit knowledge graph
- Interactive query examples
- Docker-based Dgraph setup
- Data validation and analysis tools

See the `gtfs/` directory for complete project details and implementation.

## 📰 News Knowledge Graph Import

The `news/` directory contains a comprehensive system for creating knowledge graphs from news articles using Dgraph, AI embeddings, and vector similarity search. This project converts the original HyperNews system to follow modern Python development practices.

### Prerequisites

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager
- Dgraph instance (local or remote)
- AI API keys (OpenAI, Anthropic, or Ollama for local models)
- Configuration file with Dgraph connection details

### Quick Start

```bash
# Navigate to the news project directory
cd news

# Use the automated setup script (recommended)
./setup_uv.sh

# Configure environment
make config-example
# Edit config.env with your Dgraph connection and AI API keys

# Start Dgraph (local development)
./start_dgraph.sh

# Validate system configuration
make run-validate

# Import news data
make run-import

# Generate AI embeddings
make run-embeddings

# Explore with sample queries
make run-query

# Try vector similarity search
make run-vector-search query="artificial intelligence"
```

### Documentation

- **`news/README.md`** - Original HyperNews project documentation
- **`news/docker-compose.yml`** - Dgraph and Ratel setup configuration
- **`news/schema.dql`** - Optimized Dgraph schema for news data

### Features

- Multi-provider AI support (OpenAI, Anthropic, Ollama)
- Automated news article import with entity extraction
- AI-powered semantic embeddings generation
- Vector similarity search for semantic article discovery
- Comprehensive knowledge graph with articles, topics, organizations, and locations
- Docker-based development environment with Dgraph and Ratel
- Modern Python stack with uv package management
- Data validation and testing tools

### AI Provider Support

- **OpenAI**: Full support for embeddings and chat completion
- **Anthropic**: Chat completion support (embeddings via OpenAI)
- **Ollama**: Local model support for both embeddings and chat
- **Auto-detection**: Automatically selects available provider

See the `news/` directory for complete project details and implementation.
