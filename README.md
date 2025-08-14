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
