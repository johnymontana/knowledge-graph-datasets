# GTFS to Neo4j Knowledge Graph Import

This project imports GTFS (General Transit Feed Specification) data into Neo4j, creating a comprehensive knowledge graph of transit information including agencies, routes, stops, trips, and their relationships.

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- uv (Python package manager)

## Quick Start

### 1. Start Neo4j

```bash
# Make the script executable (if not already)
chmod +x start_neo4j.sh

# Start Neo4j container
./start_neo4j.sh
```

This will start Neo4j and make it available at:
- Neo4j Browser: http://localhost:7474
- Bolt endpoint: bolt://localhost:7687
- Default credentials: neo4j/password

### 2. Configure Connection

```bash
# Create configuration from example
cp config.env.neo4j.example config.env

# Edit with your Neo4j connection details (if different from defaults)
nano config.env
```

### 3. Install Dependencies

```bash
# Install using uv
make -f Makefile.neo4j install
# OR manually
uv sync
```

### 4. Test Connection

```bash
# Test Neo4j connection
make -f Makefile.neo4j test-connection
# OR manually
uv run test_connection_neo4j.py
```

### 5. Import GTFS Data

Make sure your GTFS data files are in the `data/` directory, then run:

```bash
# Import all GTFS data
make -f Makefile.neo4j run-import
# OR manually
uv run gtfs_import_neo4j.py
```

### 6. Run Sample Queries

```bash
# Run sample Cypher queries
make -f Makefile.neo4j run-query
# OR manually
uv run sample_queries_neo4j.py
```

## Data Model

The Neo4j graph model includes these node types:

### Node Types:
- **Agency**: Transit agencies
- **Route**: Transit routes (bus, rail, etc.)
- **Stop**: Transit stops/stations
- **Trip**: Individual trips on routes
- **StopTime**: Stop times for each trip
- **Calendar**: Service schedules
- **CalendarDate**: Service exceptions
- **FareAttribute**: Fare information
- **FareRule**: Fare rules
- **Transfer**: Transfer rules between stops
- **Shape**: Route geographical shapes
- **FeedInfo**: GTFS feed metadata

### Relationships:
- `(Agency)-[:OPERATES]->(Route)`
- `(Route)-[:HAS_TRIP]->(Trip)`
- `(Trip)-[:HAS_STOP_TIME]->(StopTime)`
- `(StopTime)-[:AT_STOP]->(Stop)`
- `(Calendar)-[:SCHEDULES]->(Trip)`

## Configuration

### Connection String Format

```bash
# Standard format
NEO4J_CONNECTION_STRING=bolt://username:password@host:port/database

# Examples:
# Local Neo4j
NEO4J_CONNECTION_STRING=bolt://neo4j:password@localhost:7687/neo4j

# Neo4j Aura (cloud)
NEO4J_CONNECTION_STRING=neo4j+s://your-instance.databases.neo4j.io:7687/neo4j

# Individual components (alternative to connection string)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
```

## Sample Queries

Here are some example Cypher queries you can run:

### Find all agencies
```cypher
MATCH (a:Agency)
RETURN a.agency_name, a.agency_url
ORDER BY a.agency_name
```

### Find bus routes
```cypher
MATCH (r:Route)
WHERE r.route_type = 3  // 3 = Bus
RETURN r.route_short_name, r.route_long_name
ORDER BY r.route_short_name
```

### Find stops near a location (bounding box)
```cypher
MATCH (s:Stop)
WHERE s.stop_lat >= 47.6 AND s.stop_lat <= 47.62 
  AND s.stop_lon >= -122.35 AND s.stop_lon <= -122.33
RETURN s.stop_name, s.stop_lat, s.stop_lon
ORDER BY s.stop_name
```

### Find route with all stops
```cypher
MATCH (r:Route)-[:HAS_TRIP]->(t:Trip)-[:HAS_STOP_TIME]->(st:StopTime)-[:AT_STOP]->(s:Stop)
WHERE r.route_id = 'your_route_id'
RETURN DISTINCT r.route_short_name, s.stop_name, st.stop_sequence
ORDER BY st.stop_sequence
```

## Available Make Commands

```bash
# Using Neo4j-specific Makefile
make -f Makefile.neo4j help              # Show all commands
make -f Makefile.neo4j config            # Show current configuration
make -f Makefile.neo4j config-example    # Create config from example
make -f Makefile.neo4j install           # Install dependencies
make -f Makefile.neo4j test-connection   # Test Neo4j connection
make -f Makefile.neo4j start-neo4j       # Start Neo4j container
make -f Makefile.neo4j stop-neo4j        # Stop Neo4j container
make -f Makefile.neo4j run-import        # Import GTFS data
make -f Makefile.neo4j run-query         # Run sample queries
make -f Makefile.neo4j schema            # Apply Neo4j schema
make -f Makefile.neo4j reset-db          # Clear all data (with confirmation)
make -f Makefile.neo4j logs              # View Neo4j logs
make -f Makefile.neo4j status            # Check Neo4j status
```

## Troubleshooting

### Connection Issues

1. **Check Neo4j is running:**
   ```bash
   make -f Makefile.neo4j status
   ```

2. **Check logs:**
   ```bash
   make -f Makefile.neo4j logs
   ```

3. **Test connection:**
   ```bash
   make -f Makefile.neo4j test-connection
   ```

### Import Issues

1. **Check data directory:**
   Make sure GTFS files are in the `data/` directory

2. **Reset progress:**
   ```bash
   uv run gtfs_import_neo4j.py --reset-progress
   ```

3. **Clear database and restart:**
   ```bash
   make -f Makefile.neo4j reset-db
   make -f Makefile.neo4j run-import
   ```

### Memory Issues

If you have large GTFS datasets, you may need to:

1. **Increase Neo4j memory** in `docker-compose-neo4j.yml`:
   ```yaml
   - NEO4J_dbms_memory_heap_max__size=4G
   - NEO4J_dbms_memory_pagecache_size=2G
   ```

2. **Decrease batch size** in `config.env`:
   ```bash
   BATCH_SIZE=500
   ```

## Performance Tips

1. **Indexing**: The schema automatically creates indexes on key fields
2. **Batch Size**: Adjust `BATCH_SIZE` in config for your system
3. **Memory**: Allocate sufficient memory to Neo4j container
4. **Query Optimization**: Use `EXPLAIN` and `PROFILE` in Neo4j Browser

## Neo4j Browser

Access the Neo4j Browser at http://localhost:7474 to:
- Run interactive Cypher queries
- Visualize the graph data
- Monitor query performance
- Explore the schema

## License

This project is provided as-is for educational and development purposes.