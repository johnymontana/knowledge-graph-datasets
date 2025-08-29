# Knowledge Graph Datasets

A comprehensive collection of knowledge graph datasets and import tools for building rich, interconnected data models using modern graph databases. This repository provides ready-to-use solutions for importing various types of structured and semi-structured data into Neo4j and other graph databases.

## 📖 Available Datasets

### 🚌 GTFS Transit Data 
**Location**: `gtfs/`  
**Target Database**: Neo4j  
**Data Type**: Public Transportation Networks

Import complete GTFS (General Transit Feed Specification) transit data into Neo4j, creating comprehensive knowledge graphs of public transportation systems with routing capabilities and spatial analysis.

**Key Features:**
- Complete transit system modeling (agencies, routes, stops, trips, schedules)
- Spatial indexing for location-based queries
- Route planning and pathfinding capabilities
- Service schedule analysis and temporal queries
- Resume functionality for interrupted imports
- Real-world data from Seattle Metropolitan Area (13K+ stops, 389 routes)

**Use Cases:** Route planning, accessibility analysis, transit network optimization, urban planning

---

### 🗺️ OpenStreetMap Geospatial Data
**Location**: `openstreetmap/`  
**Target Database**: Neo4j  
**Data Type**: Geographic and Road Network Data

Import OpenStreetMap data using OSMnx to create spatial knowledge graphs with road networks, intersections, and points of interest, enabling advanced geospatial analysis and routing.

**Key Features:**
- Complete road network topology (intersections, road segments)
- Spatial relationships and geometry preservation
- Advanced routing and pathfinding algorithms
- Points of interest (restaurants, amenities, buildings)
- Real-time data fetching via OSMnx
- WKT geometry format support

**Use Cases:** Navigation systems, spatial analysis, urban planning, location-based services

---

### 📰 News Article Knowledge Graph
**Location**: `news/`  
**Target Database**: Neo4j  
**Data Type**: News Articles with AI Embeddings

Build sophisticated news knowledge graphs with AI-powered semantic analysis, entity extraction, and vector similarity search capabilities using multiple AI providers.

**Key Features:**
- Multi-provider AI support (OpenAI, Anthropic, Ollama)
- Semantic embeddings for similarity search
- Entity extraction (people, organizations, locations)
- Temporal and geospatial article analysis
- Vector similarity search with Neo4j indexes
- Topic modeling and categorization

**Use Cases:** Content recommendation, news analysis, trend detection, semantic search

---

### 🏢 Foursquare Transit & Places
**Location**: `foursquare/`  
**Target Database**: Neo4j  
**Data Type**: Points of Interest & Transit Integration

Combine Foursquare places data with transit information to analyze accessibility, walkability, and multi-modal transportation patterns in urban environments.

**Key Features:**
- Transit stop integration with places data
- Walkability and accessibility analysis
- Multi-modal routing (transit + walking)
- Business categorization and spatial relationships
- Transit desert identification
- Real-world King County Metro data

**Use Cases:** Urban accessibility, business location analysis, transit planning, walkability studies

---

### 📊 Wikidata Knowledge Graph
**Location**: `wikidata/`  
**Target Database**: Neo4j  
**Data Type**: Structured Knowledge from Wikidata

Import comprehensive knowledge graphs from Wikidata using SPARQL queries, creating rich, interconnected datasets with scientists, cities, universities, companies, and custom entities.

**Key Features:**
- Direct SPARQL integration with Wikidata endpoint
- Multiple entity types (scientists, cities, universities, companies)
- Spatial data support with Neo4j Point type
- Automatic relationship creation and schema management
- Batch processing with pagination for large datasets
- Comprehensive data validation and testing suite
- Synthetic ID system for derived entities

**Current Dataset Size:**
- **3,878 total entities** with **3,654 relationships**
- **1,540 organizations** (universities + companies)
- **1,208 places** (cities, states, countries)
- **551 people** (scientists, mayors)
- **1,537 entities with spatial coordinates**

**Use Cases:** Knowledge graph research, semantic search, entity linking, spatial analysis, academic research, business intelligence

---

### 🌐 Diffbot Knowledge Graph
**Location**: `diffbot/`  
**Target Database**: Neo4j  
**Data Type**: Web-Scale Entity Data from Diffbot API

Import comprehensive knowledge graph data from Diffbot's 10+ billion entity database into Neo4j, creating rich, interconnected datasets with organizations, people, articles, and their relationships extracted from the public web.

**Key Features:**
- **Massive Scale**: Access to 10+ billion entities from the public web
- **Entity Types**: Organizations, People, Articles, and custom entity types  
- **Rich Metadata**: Comprehensive properties including locations, industries, relationships
- **Async Processing**: High-performance concurrent API requests
- **Spatial Support**: Geographic coordinates for location-based queries
- **Flexible Queries**: Support for Diffbot's DQL (Diffbot Query Language)
- **Resume Functionality**: Paginated imports with progress tracking
- **Rate Limiting**: Built-in request throttling and retry logic

**Current Dataset Size:**
- **37 total entities** with **68 relationships**
- **18 people** (including Elon Musk and family members)
- **12 organizations** (universities, schools, political parties)
- **3 administrative areas** (countries)
- **2 education majors** and **2 degree types**

**Use Cases:** Business intelligence, competitive analysis, market research, lead generation, due diligence, content recommendation, entity resolution

## 🚀 Quick Start Guide

### Prerequisites
All projects require:
- **Python 3.8+**
- **[uv](https://docs.astral.sh/uv/)** package manager (fast Python package management)
- **Neo4j 4.0+** (or other supported graph database)
- **Docker & Docker Compose** (for local development)

### Install uv Package Manager
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Getting Started with Any Dataset

1. **Navigate to the dataset directory**:
   ```bash
   cd gtfs/          # or openstreetmap/, news/, foursquare/
   ```

2. **Run the setup script** (recommended):
   ```bash
   chmod +x setup_uv.sh
   ./setup_uv.sh
   ```

3. **Start the database** (Neo4j):
   ```bash
   chmod +x start_neo4j.sh
   ./start_neo4j.sh
   ```

4. **Configure the connection**:
   ```bash
   make config-example    # Creates example config
   nano config.env        # Edit with your settings
   ```

5. **Import the data**:
   ```bash
   make run-import        # Or use specific import commands
   ```

6. **Explore with sample queries**:
   ```bash
   make run-query         # Run example queries
   ```

## 📊 Dataset Comparison

| Dataset | Database | Data Volume | Key Relationships | Spatial Support | AI Features |
|---------|----------|-------------|------------------|-----------------|-------------|
| **GTFS** | Neo4j | 4.3M records | Agency→Route→Trip→Stop | ✅ Full GIS | ❌ |
| **OpenStreetMap** | Neo4j | Variable | Road↔Intersection, Feature↔Geometry | ✅ Full GIS | ❌ |
| **News** | Neo4j | Variable | Article↔Entity, Topic relations | ✅ Locations | ✅ Embeddings |
| **Foursquare** | Neo4j | 13K+ places | Stop↔Place, Category relations | ✅ Full GIS | ❌ |
| **Wikidata** | Neo4j | 3.9K entities | Entity↔Entity, Spatial relations | ✅ Full GIS | ❌ |
| **Diffbot** | Neo4j | 37 entities | Person→Organization, Education relations | ✅ Locations | ❌ |

## 🏗️ Common Architecture Patterns

### Data Flow Architecture
```
Raw Data → Import Scripts → Graph Database → Query Interface
    ↓           ↓              ↓              ↓
  CSV/JSON   Validation    Nodes &        Cypher/
  API Data   Processing    Relationships   Gremlin
             Batching      Indexes         Queries
```

### Technology Stack
- **Package Management**: `uv` for fast Python dependency management
- **Configuration**: Environment variables with `.env` files
- **Database**: Neo4j with spatial and vector indexes
- **Development**: Docker Compose for local development
- **Testing**: Built-in validation and sample queries
- **Documentation**: Comprehensive README files and inline docs

## 🔧 Common Configuration

All projects use consistent configuration patterns:

```bash
# Database Connection (config.env)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

# Import Settings
BATCH_SIZE=1000
DATA_DIR=data/
LOG_LEVEL=INFO

# AI Providers (news dataset)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

## 🛠️ Advanced Features

### Spatial Analysis
All geospatial datasets support:
- **Distance calculations** using `point.distance()`
- **Bounding box queries** for geographic regions
- **Spatial indexing** for fast location-based searches
- **Route planning** with graph algorithms

### Performance Optimizations
- **Batch processing** with configurable sizes
- **Resume functionality** for interrupted imports
- **Progress tracking** and status monitoring
- **Memory optimization** for large datasets
- **Index strategies** for query performance

### Wikidata Import Process
- **SPARQL Integration**: Direct connection to Wikidata's SPARQL endpoint
- **Entity Type Support**: Scientists, cities, universities, companies, and custom queries
- **Relationship Mapping**: Automatic creation of entity relationships
- **Spatial Data**: Full coordinate support with Neo4j Point type
- **Synthetic IDs**: Unique identifier system for derived entities
- **Data Validation**: Comprehensive testing suite for quality assurance

### Query Capabilities
```cypher
// Spatial proximity query
MATCH (p:Place)
WHERE distance(p.location, point({latitude: 47.6, longitude: -122.3})) < 1000
RETURN p.name, p.category

// Multi-hop relationship traversal
MATCH path = (a:Agency)-[:OPERATES]->(r:Route)-[:SERVES]->(s:Stop)
WHERE a.agency_name = "Metro Transit"
RETURN path LIMIT 10

// Vector similarity search (news dataset)
CALL db.index.vector.queryNodes('article_embeddings', 10, $queryVector)
YIELD node, score
RETURN node.title, score ORDER BY score DESC

// Wikidata knowledge graph queries
MATCH (s:Scientist)-[:WORKS_IN]->(f:Field)
WHERE f.name = "Physics"
RETURN s.name, s.birth_date, s.country

// Spatial analysis with Wikidata
MATCH (u:University)
WHERE distance(u.coordinates, point({latitude: 40.7128, longitude: -74.0060})) < 50000
RETURN u.name, distance(u.coordinates, point({latitude: 40.7128, longitude: -74.0060})) as distance_meters

// Diffbot knowledge graph queries
MATCH (p:Person)-[:EDUCATED_AT]->(o:Organization)
WHERE p.name = "Elon Musk"
RETURN p.name, o.name, o.type

// Family relationships in Diffbot
MATCH (p:Person)-[:HAS_CHILDREN]->(c:Person)
WHERE p.name = "Elon Musk"
RETURN p.name, collect(c.name) as children
```

## 📁 Project Structure

```
knowledge-graph-datasets/
├── gtfs/                    # 🚌 GTFS transit data (Neo4j)
│   ├── data/               # GTFS CSV files
│   ├── gtfs_import_neo4j.py
│   ├── sample_queries_neo4j.py
│   └── docker-compose-neo4j.yml
├── openstreetmap/          # 🗺️ OSM geospatial data (Neo4j)
│   ├── osm_import_enhanced.py
│   ├── sample_queries.py
│   └── docker-compose.yml
├── news/                   # 📰 News articles with AI (Neo4j)
│   ├── data/articles/
│   ├── news_import_neo4j.py
│   ├── news_embeddings_neo4j.py
│   └── vector_search_neo4j.py
├── foursquare/            # 🏢 Places & transit integration (Neo4j)
│   ├── data/
│   ├── foursquare_import_neo4j.py
│   └── routing_queries.py
├── wikidata/              # 📊 Wikidata knowledge graph (Neo4j)
│   ├── data/
│   ├── wikidata_import_neo4j.py
│   ├── wikidata_sparql.py
│   ├── sample_queries_neo4j.py
│   └── test_wikidata_data.py
├── diffbot/               # 🌐 Diffbot knowledge graph (Neo4j)
│   ├── data/
│   ├── diffbot_import_neo4j.py
│   ├── diffbot_client.py
│   ├── sample_queries_neo4j.py
│   └── docker-compose.yml
└── README.md              # This file
```

Each project is self-contained with its own:
- **Dependencies** (`pyproject.toml`)
- **Configuration** (`config.env.example`)  
- **Documentation** (`README.md`)
- **Sample data** (`data/` directory)
- **Docker setup** (`docker-compose.yml`)
- **Development tools** (`Makefile`)

## 🎯 Use Case Examples

### Urban Planning & Transportation
- **Transit Network Analysis**: Optimize routes and identify service gaps
- **Accessibility Studies**: Analyze wheelchair access and multi-modal connections  
- **Walkability Assessment**: Evaluate pedestrian infrastructure
- **Land Use Planning**: Correlate transit access with development patterns

### Business Intelligence & Analytics  
- **Location Intelligence**: Analyze business proximity to transportation
- **Market Research**: Understand demographic patterns and accessibility
- **Site Selection**: Find optimal locations based on transit connectivity
- **Competitive Analysis**: Map competitor locations and catchment areas

### AI & Machine Learning
- **Content Recommendation**: Semantic similarity for news articles
- **Trend Analysis**: Identify emerging topics and patterns
- **Entity Recognition**: Extract and link people, organizations, locations
- **Geospatial ML**: Predict traffic patterns, service demand

### Research & Academic
- **Social Network Analysis**: Study information flow and influence
- **Transportation Research**: Model complex transit systems
- **Urban Studies**: Analyze city development and accessibility
- **Computer Science**: Graph algorithms and spatial computing
- **Knowledge Graph Research**: Build and analyze structured knowledge graphs
- **Entity Linking**: Connect entities across different datasets and domains
- **Semantic Search**: Enable complex querying of structured knowledge

## 🤝 Contributing

We welcome contributions to expand and improve these datasets:

1. **New Datasets**: Add support for additional data sources
2. **Database Support**: Extend compatibility to other graph databases  
3. **Performance**: Optimize import scripts and query patterns
4. **Documentation**: Improve guides and add more examples
5. **Testing**: Add comprehensive test coverage

## 📄 License

This project is provided for educational and research purposes. Individual datasets may have their own licensing terms - please review the specific dataset documentation for details.

## 🆘 Support

For help with any dataset:

1. **Check the specific dataset README** in each directory
2. **Review configuration** using `make config` 
3. **Run validation tests** with `make run-validate`
4. **Check logs** for detailed error information
5. **Create an issue** on GitHub for bugs or feature requests

---

**Start building powerful knowledge graphs today! 🚀📊**
