# Knowledge Graph Datasets

This repository contains various knowledge graph datasets and import tools for building comprehensive knowledge graphs using Dgraph.

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

- **`gtfs/README.md`** - Detailed usage instructions
- **`gtfs/docker-compose.yml`** - Dgraph setup configuration

### Features

- Complete GTFS data import into Dgraph
- Comprehensive transit knowledge graph
- Interactive query examples
- Docker-based Dgraph setup
- Data validation and analysis tools

See the `gtfs/` directory for complete project details and implementation.

## 🗺️ OpenStreetMap Geospatial Data Import

The OpenStreetMap project is located in the `openstreetmap/` directory and provides a complete solution for importing OpenStreetMap (OSM) data into Dgraph using the OSMnx Python package.

### Prerequisites

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager
- Dgraph instance (local or remote)
- Configuration file with Dgraph connection details

### Quick Start

```bash
# Navigate to the OSM project directory
cd openstreetmap

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

# Validate OSM data access
uvx run test_osm_data.py

# Import OSM data to Dgraph
uvx run osm_import.py

# Explore with sample queries
uvx run sample_queries.py
```

### Documentation

- **`openstreetmap/README.md`** - Detailed usage instructions
- **`openstreetmap/docker-compose.yml`** - Dgraph setup configuration

### Features

- Geospatial OSM data import into Dgraph using OSMnx
- Support for various OSM data types (amenities, buildings, parks, etc.)
- RDF conversion with spatial geometry preservation
- Interactive spatial and attribute-based queries
- Docker-based Dgraph setup
- Data validation and testing tools

See the `openstreetmap/` directory for complete project details and implementation.

## 🔧 Common Setup for All Projects

Both projects use the same modern tooling and follow similar patterns:

### Package Management
- **uv** for fast Python package management
- **pyproject.toml** for modern Python packaging
- **Makefile** for project management commands

### Dgraph Integration
- **Docker Compose** for local Dgraph development
- **Configuration management** with environment variables
- **Health checks** and automated startup scripts

### Development Tools
- **Black** for code formatting
- **Flake8** for linting
- **Pytest** for testing
- **Comprehensive logging** and error handling

## 📚 Project Structure

```
knowledge-graph-datasets/
├── gtfs/                    # GTFS transit data import project
├── openstreetmap/           # OpenStreetMap geospatial data import project
├── news/                    # News article knowledge graph project
└── README.md                # This file
```

Each project directory contains a complete, self-contained implementation with its own documentation, configuration, and tooling.
