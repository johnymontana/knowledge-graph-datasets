# 📊 Wikidata Knowledge Graph Import for Neo4j

Import structured knowledge from [Wikidata](https://www.wikidata.org/) into Neo4j using SPARQL queries to create rich, interconnected knowledge graphs. This project provides a complete solution for querying the Wikidata SPARQL endpoint and transforming the results into a Neo4j graph database.

## 🚀 Features

- **🔍 SPARQL Query Integration**: Direct connection to Wikidata's SPARQL endpoint
- **📈 Flexible Entity Types**: Import scientists, cities, universities, companies, or custom queries  
- **🌍 Spatial Support**: Full geographic coordinate handling and spatial indexing
- **🔗 Relationship Mapping**: Automatic relationship creation (citizenship, location, occupation, etc.)
- **📦 Batch Processing**: Efficient import with configurable batch sizes and pagination
- **🏗️ Schema Management**: Automated constraint and index creation for optimal performance
- **✅ Data Validation**: Comprehensive test suite for data quality assurance
- **⚡ Performance Optimization**: Spatial indexes, full-text search, and query optimization

## 📊 **Current Knowledge Graph Statistics**

Our successful import has created a comprehensive knowledge graph with:

- **3,878 total entities** 
- **3,654 relationships**
- **1,540 organizations** (universities + companies)
- **1,208 places** (cities, states, countries)
- **551 people** (scientists, mayors)
- **1,537 entities with spatial coordinates**
- **907 cities** with population and state data
- **202 scientists** with field and country relationships
- **All entities have proper Wikidata IDs** (both real Q/P IDs and synthetic IDs for derived entities)

## 📋 Quick Start

### 1. Prerequisites

- **Python 3.8+**
- **[uv](https://docs.astral.sh/uv/)** package manager
- **Neo4j 4.0+** (local or remote instance)
- **Internet connection** for Wikidata SPARQL queries

### 2. Setup

```bash
# Clone the repository and navigate to wikidata directory
cd wikidata/

# Install dependencies with uv
uv sync

# Configure connection settings
cp config.env.example config.env
nano config.env  # Edit with your Neo4j credentials
```

### 3. Import Data

```bash
# Test connection
uv run python test_wikidata_data.py

# Import scientists (default)
uv run python wikidata_import_neo4j.py --query-type scientists --limit 1000

# Import different entity types
uv run python wikidata_import_neo4j.py --query-type cities --limit 1000
uv run python wikidata_import_neo4j.py --query-type universities --limit 1000
uv run python wikidata_import_neo4j.py --query-type companies --limit 1000

# Run custom SPARQL query
uv run python wikidata_import_neo4j.py --query-type custom --sparql-file my_query.sparql
```

### 4. Explore Data

```bash
# Run sample queries
uv run python sample_queries_neo4j.py

# Validate data quality
uv run python test_wikidata_data.py
```

## 🎯 Supported Entity Types

### 👨‍🔬 Scientists
Import scientists with biographical information, fields of work, and citizenship:
```sparql
SELECT ?item ?itemLabel ?birthDate ?deathDate ?fieldLabel ?countryLabel ?coordinates
WHERE {
  ?item wdt:P31 wd:Q5 .        # human
  ?item wdt:P106 wd:Q901 .     # occupation: scientist
  # ... additional properties
}
```

**Example entities**: Einstein, Curie, Newton, Tesla  
**Relationships**: `WORKS_IN` → Field, `CITIZEN_OF` → Country

**Import Results**: Successfully imported 1,000 scientists with field and country relationships

### 🏙️ Cities  
Import cities with population, geographic, and administrative data:
```sparql
SELECT ?item ?itemLabel ?population ?coordinates ?stateLabel ?mayorLabel
WHERE {
  ?item wdt:P31/wdt:P279* wd:Q515 .  # city
  ?item wdt:P17 wd:Q30 .             # country (US by default)
  # ... additional properties
}
```

**Example entities**: New York, Los Angeles, Chicago, Houston  
**Relationships**: `LOCATED_IN` → State, `MAYOR_OF` ← Person

**Import Results**: Successfully imported 1,000 cities with population, state, and mayor data

### 🎓 Universities
Import universities with founding dates, student counts, and locations:
```sparql  
SELECT ?item ?itemLabel ?countryLabel ?coordinates ?founded ?studentsCount
WHERE {
  ?item wdt:P31/wdt:P279* wd:Q3918 .  # university
  # ... additional properties  
}
```

**Example entities**: Harvard, MIT, Stanford, Oxford  
**Relationships**: `LOCATED_IN` → Country

**Import Results**: Successfully imported 1,000 universities with founding dates and country relationships

### 🏢 Companies
Import companies with founding information and geographic data:
```sparql
SELECT ?item ?itemLabel ?countryLabel ?coordinates ?founded ?ceo ?industry
WHERE {
  ?item wdt:P31/wdt:P279* wd:Q4830453 .  # business enterprise
  # ... additional properties
}
```

**Example entities**: Apple, Google, Microsoft, Tesla  
**Relationships**: `LOCATED_IN` → Country

**Import Results**: Successfully imported 1,000 companies with founding dates and country relationships

## 🔧 Configuration

### Environment Variables (`config.env`)

```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=letmeinnow
NEO4J_DATABASE=neo4j

# Import Settings
BATCH_SIZE=1000
LOG_LEVEL=INFO
DATA_DIR=data/

# Wikidata SPARQL
WIKIDATA_ENDPOINT=https://query.wikidata.org/sparql
REQUEST_DELAY=1.0        # Delay between requests (be respectful!)
MAX_RETRIES=3
TIMEOUT=30
```

### Custom SPARQL Queries

Create custom queries by extending the `WikidataQueries` class or providing SPARQL files:

```python
# In wikidata_sparql.py
@staticmethod
def get_custom_entities(limit: int = 1000) -> str:
    return f"""
    SELECT ?item ?itemLabel ?customProperty WHERE {{
        ?item wdt:P31 wd:YourEntityType .
        ?item wdt:PCustom ?customProperty .
        SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" . 
        }}
    }} LIMIT {limit}
    """
```

## 📊 Data Model

### Node Labels
- **Entity**: Base label for all imported entities
- **Person**: People (scientists, mayors, CEOs, etc.)
- **Place**: Geographic locations (cities, states, countries)
- **Organization**: Institutions (universities, companies)
- **Field**: Areas of scientific work

### Key Properties
- `wikidata_id`: Unique Wikidata identifier (Q123, P456) or synthetic ID for derived entities
- `name/label`: Human-readable name
- `coordinates`: Geographic point data using Neo4j Point type
- `type`: Entity classification
- `updated_at`: Import timestamp

### Relationships
- `WORKS_IN`: Person → Field
- `CITIZEN_OF`: Person → Country  
- `LOCATED_IN`: Place/Organization → Place
- `MAYOR_OF`: Person → City

### Synthetic ID System
For derived entities (fields, countries, states, mayors), we generate synthetic IDs:
- **Fields**: `FIELD_Physics`, `FIELD_Biology`
- **Countries**: `COUNTRY_United_States`, `COUNTRY_Japan`
- **States**: `STATE_California`, `STATE_Texas`
- **Mayors**: `MAYOR_John_Smith`

## 🔍 Sample Queries

### Basic Entity Exploration
```cypher
// Count entities by type
MATCH (n:Entity)
RETURN n.type, count(*) as count
ORDER BY count DESC
```

### Spatial Queries
```cypher
// Find entities near a location (within 50km of San Francisco)
MATCH (n:Entity)
WHERE n.coordinates IS NOT NULL
WITH n, point({latitude: 37.7749, longitude: -122.4194}) as sf,
     point(n.coordinates) as entity_point
WITH n, distance(sf, entity_point) as distance_meters
WHERE distance_meters < 50000
RETURN n.name, n.type, distance_meters
ORDER BY distance_meters
```

### Relationship Analysis
```cypher
// Scientists by field of work
MATCH (p:Person {occupation: 'Scientist'})-[:WORKS_IN]->(f:Field)
RETURN f.name as field, count(p) as scientist_count
ORDER BY scientist_count DESC
```

### Full-Text Search
```cypher
// Search entities by name
CALL db.index.fulltext.queryNodes("entity_fulltext_idx", "Einstein")
YIELD node, score
RETURN node.name, node.type, score
ORDER BY score DESC
```

## 🏗️ Schema & Performance

### Automatic Schema Creation
The import process creates optimized schema elements:

- **Uniqueness Constraints**: Ensure data integrity on `wikidata_id`
- **Property Indexes**: Fast lookups on names, types, dates
- **Spatial Indexes**: Geographic coordinate queries  
- **Full-Text Indexes**: Search across names and descriptions
- **Composite Indexes**: Multi-property query optimization

### Performance Features
- **Batch Processing**: Configurable batch sizes for large imports
- **Pagination**: Handle large result sets from SPARQL endpoint
- **Connection Pooling**: Efficient Neo4j connection management
- **Query Optimization**: Pre-built indexes for common query patterns
- **Rate Limiting**: Respectful API usage with configurable delays

## 📈 Usage Examples

### Import 10,000 Scientists
```bash
uv run python wikidata_import_neo4j.py --query-type scientists --limit 10000
```

### Import US Cities with Custom Batch Size  
```bash
BATCH_SIZE=500 uv run python wikidata_import_neo4j.py --query-type cities --limit 5000
```

### Use Custom SPARQL Query
```bash
uv run python wikidata_import_neo4j.py --query-type custom --sparql-file my_query.sparql
```

### Validate Data Quality
```bash
uv run python test_wikidata_data.py
```

## 🧪 Testing & Validation

The project includes comprehensive data validation:

- **Connection Testing**: Verify Neo4j connectivity
- **Data Integrity**: Check for required fields and valid formats  
- **Schema Validation**: Ensure constraints and indexes exist
- **Relationship Testing**: Verify graph structure integrity
- **Spatial Data**: Validate coordinate ranges and formats
- **Performance Testing**: Query execution time analysis

```bash
# Run all validation tests
uv run python test_wikidata_data.py

# Expected output: All 11 tests should pass ✅
```

## 🔄 Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make setup` | Install dependencies and setup environment |
| `make start` | Start Neo4j database |
| `make test-connection` | Test Neo4j connection |
| `make run-import` | Import scientists (default) |
| `make import-cities` | Import US cities |
| `make import-universities` | Import universities |  
| `make import-companies` | Import companies |
| `make run-query` | Run sample queries |
| `make schema` | Create schema and indexes |
| `make validate-data` | Run data validation tests |
| `make clean` | Remove imported data |

## 🌐 Integration Examples

### With GraphRAG Applications
```python
from wikidata_sparql import WikidataSPARQLClient

client = WikidataSPARQLClient()
scientist_data = client.query_to_dataframe(
    WikidataQueries.get_scientists(limit=1000)
)

# Integrate with your GraphRAG pipeline
```

### With Spatial Applications
```cypher
// Find universities near tech companies
MATCH (u:University)
WHERE u.coordinates IS NOT NULL

MATCH (c:Company)
WHERE c.coordinates IS NOT NULL 
  AND distance(point(u.coordinates), point(c.coordinates)) < 10000

RETURN u.name, c.name, 
       distance(point(u.coordinates), point(c.coordinates)) as distance_meters
```

### With Data Science Workflows
```python
# Export to pandas for analysis
from sample_queries_neo4j import WikidataNeo4jQueries

queries = WikidataNeo4jQueries()
results = queries.run_query("""
    MATCH (p:Person {occupation: 'Scientist'})-[:CITIZEN_OF]->(c:Country)
    RETURN c.name as country, count(p) as scientist_count
    ORDER BY scientist_count DESC
""")

# Convert to DataFrame for analysis
import pandas as pd
df = pd.DataFrame(results)
```

## ⚠️ Rate Limiting & Ethics

This project is designed to be respectful of Wikidata's infrastructure:

- **Default 1-second delay** between SPARQL requests
- **Configurable request timeouts** and retry logic
- **User-Agent identification** for responsible usage
- **Batch size limits** to prevent endpoint overload

Please review [Wikidata's usage guidelines](https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/Wikidata_Query_Help) and use this tool responsibly.

## 🔧 **Recent Fixes & Improvements**

During our successful import process, we resolved several technical challenges:

1. **SPARQL Query LIMIT Conflict** - Fixed duplicate LIMIT clauses in SPARQL queries
2. **Coordinate Format** - Fixed coordinate parsing to use Neo4j Point type for spatial data
3. **Variable Naming Conflicts** - Resolved Cypher variable naming conflicts in import methods
4. **Constraint Conflicts** - Fixed label conflicts between Entity, Place, and Organization nodes
5. **Synthetic ID Generation** - Created unique ID system for derived entities (Field, Country, State, etc.)

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- **Additional entity types** (books, movies, events, etc.)
- **Enhanced relationship extraction** from Wikidata properties
- **Multi-language support** for labels and descriptions  
- **Real-time update mechanisms** for keeping data current
- **Performance optimizations** for very large imports

## 📄 License

This project is provided for educational and research purposes. Please respect Wikidata's [licensing terms](https://www.wikidata.org/wiki/Wikidata:Licensing) for any data usage.

## 🆘 Troubleshooting

### Common Issues

**Connection Errors**
```bash
# Check Neo4j status
docker ps
docker logs neo4j-wikidata

# Test connection
uv run python test_wikidata_data.py
```

**SPARQL Timeouts**
```bash
# Increase timeout in config.env
TIMEOUT=60
REQUEST_DELAY=2.0

# Use smaller batch sizes
BATCH_SIZE=500
```

**Memory Issues**
```bash
# Increase Neo4j memory in docker-compose.yml
NEO4J_dbms_memory_heap_max__size: 8G
NEO4J_dbms_memory_pagecache_size: 4G
```

**Import Failures**
```bash
# Check logs for specific errors
tail -f logs/import.log

# Validate data after partial import
uv run python test_wikidata_data.py

# Clean and restart if needed
make clean
uv run python wikidata_import_neo4j.py --query-type scientists --limit 1000
```

### Getting Help

1. **Check the logs** for detailed error information
2. **Review configuration** in `config.env`  
3. **Run validation tests** to identify data issues
4. **Consult Wikidata documentation** for SPARQL query help
5. **Create an issue** on GitHub for bugs or feature requests

---

**Start building your Wikidata knowledge graph today! 🚀📊**

*Successfully tested with 3,878 entities and 3,654 relationships across scientists, cities, universities, and companies.*