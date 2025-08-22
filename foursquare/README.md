# Foursquare Transit and Places Data for Neo4j

This directory contains tools for importing Foursquare transit stops and places data into Neo4j, with a focus on geospatial analysis and routing capabilities.

## Dataset Overview

The dataset includes:
- **Transit Stops** (`stops.txt`): King County Metro transit stops with geospatial coordinates
- **Places** (`king_county_places_near_stops.csv`): Points of interest from Foursquare API near transit stops

## Key Features

- 🗺️ **Geospatial Analysis**: Advanced location-based queries using Neo4j spatial functions
- 🚌 **Transit Accessibility**: Analysis of places accessible by public transit
- 🔍 **Routing Capabilities**: Multi-modal routing between transit stops and places
- 📊 **Business Intelligence**: Demographics and accessibility insights
- 🏃 **Walkability Analysis**: Places within walking distance calculations

## Data Schema

### Node Types
- **TransitStop**: King County Metro bus stops and stations
- **Place**: Points of interest from Foursquare (restaurants, shops, services, etc.)
- **Category**: Foursquare place categories

### Relationships
- **BELONGS_TO_CATEGORY**: Place → Category
- **NEAR_STOP**: Place → TransitStop (named relationship from dataset)
- **WITHIN_500M**: Place ↔ TransitStop (spatial proximity)
- **WITHIN_WALKING_DISTANCE**: Places within 800m walking distance

### Key Properties
- **Geospatial**: All places and stops include `latitude/longitude` and `location` (Neo4j Point)
- **Categories**: Places linked to Foursquare category hierarchy
- **Transit Info**: Stop names, codes, zones, accessibility info
- **Place Details**: Names, addresses, contact info, business hours

## Installation & Setup

### Prerequisites
- Python 3.7+
- Neo4j 4.0+ (with APOC plugin recommended)
- Required Python packages: `neo4j`, `pandas`, `python-dotenv`

### Install Dependencies
```bash
cd foursquare/
pip install neo4j pandas python-dotenv
```

### Configure Neo4j Connection
Create a `config.env` file:
```env
NEO4J_CONNECTION_STRING=bolt://username:password@localhost:7687/neo4j
```

Or set environment variables:
```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=your_password
export NEO4J_DATABASE=neo4j
```

## Usage

### Import Data
```bash
# Import all data with default settings
python foursquare_import_neo4j.py

# Custom data directory and batch size
python foursquare_import_neo4j.py --data-dir ./data --batch-size 500

# Use custom config file
python foursquare_import_neo4j.py --config-file my_config.env
```

### Run Sample Queries
```bash
# Run all sample queries
python sample_queries_neo4j.py
```

### Apply Schema
```bash
# Apply schema manually using Neo4j Browser or cypher-shell
cypher-shell < neo4j_schema.cypher
```

## Sample Queries & Use Cases

### 1. Find Places Near Transit
```cypher
// Find restaurants within 500m of Westlake Station
MATCH (ts:TransitStop {stop_name: "Westlake Station"})-[:WITHIN_500M]-(p:Place)-[:BELONGS_TO_CATEGORY]->(c:Category)
WHERE c.label CONTAINS "Restaurant"
RETURN p.name, p.address, c.label
```

### 2. Transit Accessibility Analysis
```cypher
// Places with best transit connectivity
MATCH (p:Place)-[:WITHIN_500M]->(ts:TransitStop)
RETURN p.name, p.locality, count(ts) as transit_connections
ORDER BY transit_connections DESC
LIMIT 10
```

### 3. Spatial Distance Queries
```cypher
// Places within 1km of downtown Seattle
WITH point({latitude: 47.6062, longitude: -122.3321}) as downtown
MATCH (p:Place)
WHERE distance(p.location, downtown) <= 1000
RETURN p.name, round(distance(p.location, downtown)) as distance_meters
ORDER BY distance_meters
```

### 4. Multi-Modal Routing
```cypher
// Route from transit stop to restaurants (max 2 hops)
MATCH path = (start:TransitStop {stop_name: "3rd Ave & Pike St"})-[:WITHIN_500M*1..2]-(p:Place)-[:BELONGS_TO_CATEGORY]->(c:Category)
WHERE c.label CONTAINS "Restaurant"
RETURN p.name, c.label, length(path) as hops
ORDER BY hops, p.name
```

### 5. Walkability Analysis
```cypher
// Places with most nearby amenities (walkable neighborhoods)
MATCH (p:Place)
OPTIONAL MATCH (p)-[:WITHIN_500M]-(neighbor:Place)-[:BELONGS_TO_CATEGORY]->(c:Category)
WHERE c.label CONTAINS "Restaurant" OR c.label CONTAINS "Shop"
RETURN p.name, p.locality, count(neighbor) as nearby_amenities
ORDER BY nearby_amenities DESC
```

### 6. Transit Desert Analysis
```cypher
// Areas with poor transit access
MATCH (p:Place)
OPTIONAL MATCH (p)-[:WITHIN_500M]->(ts:TransitStop)
WITH p.locality, count(p) as total_places, count(ts) as transit_connections
WHERE total_places >= 5
RETURN locality, total_places, transit_connections,
       round(100.0 * transit_connections / total_places) as coverage_percent
ORDER BY coverage_percent
```

## Advanced Geospatial Capabilities

### Spatial Indexes
The schema creates spatial indexes for efficient location queries:
- Point indexes on `location` properties
- Composite indexes on coordinates
- Text indexes for location names

### Distance-Based Relationships
Relationships are created based on spatial proximity:
- `WITHIN_500M`: Places within 500 meters
- `WITHIN_WALKING_DISTANCE`: Typical walking distance (800m)
- `WITHIN_1KM`: Nearby locations for broader analysis

### Routing Algorithms
Use Neo4j's graph algorithms for:
- Shortest path between transit stops
- Multi-modal routing (transit + walking)
- Accessibility analysis
- Service area coverage

## Data Sources

- **Transit Data**: King County Metro GTFS data
- **Places Data**: Foursquare Places API
- **Categories**: Foursquare category taxonomy
- **Geospatial**: WGS84 coordinate system (SRID 4326)

## Schema Visualization

```
(TransitStop)--[WITHIN_500M]--(Place)--[BELONGS_TO_CATEGORY]-->(Category)
     |                           |
  location                   location
  stop_name                    name
  zone_id                   address
                            locality
```

## Performance Tips

1. **Use Spatial Indexes**: Ensure point indexes are created for location properties
2. **Limit Distance Queries**: Use reasonable distance limits (< 10km)
3. **Batch Operations**: Use batch size of 1000-5000 for imports
4. **Query Optimization**: Use `PROFILE` to analyze query performance

## Extension Ideas

- **Real-time Transit**: Integrate with King County Metro real-time API
- **Route Planning**: Add GTFS route and schedule data
- **User Preferences**: Add user profiles and preference matching
- **Business Hours**: Time-based availability queries
- **Reviews Integration**: Add Foursquare ratings and reviews
- **Weather Data**: Weather-aware routing recommendations

## Troubleshooting

### Common Issues
1. **Memory Errors**: Reduce batch size or increase Java heap size
2. **Connection Timeouts**: Check Neo4j server status and firewall
3. **Spatial Query Errors**: Ensure Neo4j 4.0+ and proper spatial configuration
4. **Missing Data**: Verify CSV files are in the correct directory

### Performance Optimization
```cypher
// Check index usage
PROFILE MATCH (p:Place) 
WHERE distance(p.location, point({x: -122.33, y: 47.61})) < 1000 
RETURN count(p)

// Monitor memory usage
CALL dbms.listQueries() YIELD queryId, query, elapsedTimeMillis, allocatedBytes
```

For additional support, see the main project documentation or create an issue on GitHub.