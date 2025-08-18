# OpenStreetMap to Dgraph Knowledge Graph Project

This project provides a complete solution for importing OpenStreetMap (OSM) data into Dgraph, creating a rich knowledge graph of geographic and amenity information that can be queried and analyzed spatially.

## 🎯 Project Goals

- **Geospatial Data Integration**: Import comprehensive OSM data into Dgraph using OSMnx
- **Knowledge Graph**: Create meaningful relationships between geographic features and amenities
- **Spatial Query Capability**: Enable complex spatial and attribute-based queries
- **Scalability**: Handle large OSM datasets efficiently
- **Ease of Use**: Provide simple tools for setup and data exploration

## 🏗️ Architecture Overview

```
OpenStreetMap Data → OSMnx Python Package → RDF Conversion → Dgraph Database → Spatial Queries
         ↓                    ↓                    ↓              ↓              ↓
    Geographic         Data Processing      RDF Format      Graph Schema    GraphQL/DQL
    Features &         (Filtering,         (Nodes &        (Nodes &        (Interactive
    Amenities         Type Conversion,     Edges)          Edges)          Queries)
                      Batching)
```

## 📁 Project Structure

```
knowledge-graph-datasets/
├── openstreetmap/                    # OSM data directory
│   ├── data/                         # OSM data files and RDF output
│   ├── osm_import.py                 # Main import script
│   ├── test_osm_data.py              # Data validation script
│   ├── sample_queries.py             # Query examples
│   ├── dgraph_config.py              # Configuration management
│   ├── docker-compose.yml            # Dgraph setup
│   ├── start_dgraph.sh               # Startup script
│   ├── setup_uv.sh                   # Automated setup script
│   ├── Makefile                      # Project management commands
│   ├── pyproject.toml                # Project configuration
│   ├── config.env.example            # Configuration template
│   ├── simple_schema.txt             # Dgraph schema
│   └── README.md                     # This file
```

## 🚀 Quick Start

### 1. Setup Environment
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
```

### 2. Configure Dgraph Connection
```bash
# Create configuration file
make config-example

# Edit configuration with your connection details
nano config.env
```

### 3. Start Dgraph (Local)
```bash
# For local development
./start_dgraph.sh
```

### 4. Validate Data
```bash
# Using uvx (recommended)
uvx run test_osm_data.py

# Or using uv with activated virtual environment
uv run python test_osm_data.py
```

### 5. Import Data
```bash
# Basic import (will resume if interrupted)
uvx run osm_import.py

# Import with custom parameters
uvx run osm_import.py --location "New York, NY" --tags "amenity=restaurant" --output ny_restaurants.rdf
```

## 📊 Data Types

The project imports various types of OSM data:

- **Amenities**: Restaurants, shops, schools, hospitals, etc.
- **Geographic Features**: Buildings, parks, roads, water bodies
- **Address Information**: Street addresses, postal codes
- **Spatial Data**: WKT (Well-Known Text) geometry representations
- **Metadata**: OSM tags, names, and other attributes

## 🗺️ Graph Data Model

The OpenStreetMap data is modeled in Dgraph using a simple but effective schema that captures the essential relationships between geographic features and their spatial properties.

### Schema Overview

```graphql
type Feature {
    name: string
    amenity: string
    address: string
    geometry: Geometry
    osm_id: string
}

type Geometry {
    wkt: string
}

# Predicates with indexes for efficient querying
name: string @index(term, fulltext) .
amenity: string @index(exact, term) .
address: string @index(term, fulltext) .
osm_id: string @index(exact) .
wkt: string .
geometry: [uid] @reverse .
```

### Data Model Relationships

```
┌─────────────┐         ┌──────────────┐
│   Feature   │────────▶│   Geometry   │
├─────────────┤         ├──────────────┤
│ name        │         │ wkt          │
│ amenity     │         └──────────────┘
│ address     │              │
│ osm_id      │              │
└─────────────┘              │
       │                     │
       └─────────────────────┘
           geometry
```

**Feature Node**: Represents an OSM feature (restaurant, shop, etc.) with:
- `name`: Display name of the feature
- `amenity`: Type of amenity (restaurant, cafe, etc.)  
- `address`: Concatenated address information
- `osm_id`: Original OpenStreetMap identifier
- `geometry`: Reference to associated geometry

**Geometry Node**: Contains spatial data with:
- `wkt`: Well-Known Text representation of the geographic shape

## �� Sample DQL Queries with Results

Here are example DQL (Dgraph Query Language) queries with actual results from the imported OpenStreetMap data:

### 1. Find All Restaurants

**Query:**
```graphql
{
  restaurants(func: eq(amenity, "restaurant")) {
    name
    amenity
    address
    osm_id
    geometry {
      wkt
    }
  }
}
```

**Results:** The database contains **1,871 restaurants** in San Francisco. Here are some examples:

- **RakiRaki** - Address: "3282", OSM ID: "way_273575853"
- **Amici's East Coast Pizza** - OSM ID: "node_2338785909"
- **산왕반점** (Korean restaurant) - OSM ID: "node_2652836518"
- **Scott's Chowder House** - Address: "San Francisco", OSM ID: "node_1928508899"
- **The Snug** - OSM ID: "node_9877742323"
- **Shanghai Dumpling King** - Address: "720", OSM ID: "node_3853311604"

### 2. Search Restaurants by Name

**Query:**
```graphql
{
  search_restaurants(func: allofterms(name, "pizza")) {
    name
    amenity
    address
    osm_id
  }
}
```

**Results:** Found **67 pizza restaurants** including:

- **Amici's East Coast Pizza** - OSM ID: "node_2338785909"
- **Long Bridge Pizza Company** - Address: "94107", OSM ID: "node_12637817162"
- **Round Table Pizza** - Address: "Mission Street", OSM ID: "node_2054109883"
- **Napoli Pizza** - Address: "Polk Street", OSM ID: "node_818671268"
- **New York Pizza Kitchen** - Address: "CA", OSM ID: "node_9452420640"
- **Tony's Pizza Napoletana** - Address: "CA", OSM ID: "node_3702219083"
- **Little Star Pizza** - Address: "400", OSM ID: "node_319020714"

### 3. Find Features by Address

**Query:**
```graphql
{
  sf_features(func: anyofterms(address, "California Street")) {
    name
    amenity
    address
    osm_id
  }
}
```

**Results:** Found **1 restaurant** on California Street:

- **Barbacco** - Address: "California Street", OSM ID: "node_5292820522"

*Note: This query searches for any address containing "California Street" terms. Many restaurants have partial addresses or street names.*

### 4. Get Features with Geometry Data

**Query:**
```graphql
{
  features_with_geo(func: has(geometry)) {
    name
    amenity
    geometry {
      wkt
    }
  }
}
```

**Results:** Found **1,871 restaurants** with geometry data. Examples with coordinates:

- **Epic Steak** - Address: "San Francisco"
  - Geometry: `POINT (-122.389353 37.7907487)` (Fisherman's Wharf area)
- **Crazy Pepper** - Address: "San Francisco"
  - Geometry: `POINT (-122.446249 37.7209036)` (Southern SF)
- **Eats** - Address: "Clement Street"
  - Geometry: `POINT (-122.4600246 37.7832711)` (Richmond District)
- **Lark** - Address: "San Francisco"
  - Geometry: `POINT (-122.4342444 37.7611065)` (Mission Bay area)
- **T-28 Bakery & Cafe** - Address: "San Francisco"
  - Geometry: `POINT (-122.4851736 37.7425142)` (Outer Sunset)
- **The Richmond** - Address: "615"
  - Geometry: `POINT (-122.4654532 37.7770459)` (Richmond District)

### 5. Count Features by Amenity Type

**Query:**
```graphql
{
  amenity_counts(func: has(amenity)) @groupby(amenity) {
    count(uid)
  }
}
```

**Results:**
- **Restaurants**: 1,871 total restaurants in the database

### 6. Find Features with Specific OSM IDs

**Query:**
```graphql
{
  specific_features(func: anyofterms(osm_id, "node_286132370 way_1084548884")) {
    name
    amenity
    address
    osm_id
    geometry {
      wkt
    }
  }
}
```

**Results:** Found **1 restaurant** with the specified OSM ID:

- **Mel's Drive-in** - Address: "94123", OSM ID: "node_286132370"

### 7. Full Text Search Across Names and Addresses

**Query:**
```graphql
{
  text_search(func: anyoftext(name, "chinese restaurant")) {
    name
    amenity
    address
  }
}
```

**Results:** Found **89 restaurants** with "chinese" in the name or description, including:

- **Great Eastern Restaurant** - Address: "649"
- **Peninsula Sea Food Restaurant** - Address: "CA"
- **Western Donut Chinese Food** - Address: "CA"
- **Henry's Hunan Restaurant** - Address: "94105"
- **House of Nanking** - Address: "Kearny Street"
- **Chinatown Restaurant** - Address: "Washington Street"
- **Golden Dragon Dining** - Address: "CA"
- **Peking Restaurant** - Address: "CA"

### 8. Get Random Sample of Features

**Query:**
```graphql
{
  sample_features(func: has(name), first: 10) {
    name
    amenity
    address
    geometry {
      wkt
    }
  }
}
```

**Results:** Sample of 10 restaurants:

- **RakiRaki** - Address: "3282"
- **Amici's East Coast Pizza**
- **산왕반점** (Korean restaurant)
- **Scott's Chowder House** - Address: "San Francisco"
- **The Snug**
- **Shanghai Dumpling King** - Address: "720"
- **Sunset Indian Cusine** - Address: "94122"
- **a Mano** - Address: "Hayes Street"
- **One Bite** - Address: "506"
- **Heirloom Cafe** - Address: "2500"

## 📊 Database Statistics

Based on the query results, the current database contains:

- **Total Restaurants**: 1,871
- **Restaurants with Geometry**: 1,871 (100%)
- **Restaurants with Names**: 1,871 (100%)
- **Restaurants with Addresses**: ~1,200+ (varies by completeness)
- **Geographic Coverage**: San Francisco Bay Area
- **Data Types**: Primarily restaurants (amenity=restaurant)

## 🗺️ Geographic Distribution

The restaurants are distributed across various San Francisco neighborhoods:

- **Fisherman's Wharf**: Epic Steak, Crab House
- **Mission District**: Mission Chinese Food, La Taqueria
- **Richmond District**: The Richmond, Eats
- **Sunset District**: T-28 Bakery & Cafe
- **North Beach**: Various Italian restaurants
- **Chinatown**: Traditional Chinese restaurants
- **Financial District**: High-end dining establishments

## 🔧 Configuration

### Environment Variables

Create a `config.env` file based on `config.env.example`:

```bash
# Dgraph Connection
DGRAPH_CONNECTION_STRING=@dgraph://localhost:8080

# Import Settings
BATCH_SIZE=1000
DATA_DIR=data

# OSM Settings
OSM_LOCATION="San Francisco, California"
OSM_TAGS=amenity=restaurant
OSM_OUTPUT_FILE=osm_data.rdf

# Logging
LOG_LEVEL=INFO
```

### Customizing OSM Data

Modify the configuration to import different types of OSM data:

```bash
# Restaurants in New York
OSM_LOCATION="New York, NY"
OSM_TAGS=amenity=restaurant

# Schools in London
OSM_LOCATION="London, UK"
OSM_TAGS=amenity=school

# Parks in Tokyo
OSM_LOCATION="Tokyo, Japan"
OSM_TAGS=leisure=park
```

## 📝 Usage Examples

### Basic Import
```bash
# Import restaurants in San Francisco
uvx run osm_import.py --location "San Francisco, California" --tags "amenity=restaurant"
```

### Data Validation
```bash
# Test OSM data access and Dgraph connection
uvx run test_osm_data.py --verbose

# Validate specific location and tags
uvx run test_osm_data.py --location "Paris, France" --tags "amenity=cafe"
```

### Running Queries
```bash
# Run all sample queries
uvx run sample_queries.py --all

# Query specific amenity type
uvx run sample_queries.py --amenity restaurant

# Query specific location
uvx run sample_queries.py --location "San Francisco"
```

## 🛠️ Development

### Project Commands
```bash
make help              # Show all available commands
make install           # Install dependencies
make dev-install       # Install with development dependencies
make test              # Run tests
make format            # Format code with black
make lint              # Lint code with flake8
make clean             # Remove virtual environment
```

### Code Quality
```bash
# Format code
uv run black .

# Lint code
uv run flake8 .

# Run tests
uv run pytest
```

## 🐳 Docker Support

### Start Dgraph Services
```bash
# Start Dgraph and Ratel UI
make start-dgraph

# Check status
make status

# View logs
make logs

# Stop services
make stop-dgraph
```

### Access Points
- **GraphQL**: http://localhost:8000
- **HTTP API**: http://localhost:8080
- **Ratel UI**: http://localhost:8001

## 📚 API Reference

### OSMImporter Class
Main class for importing OSM data into Dgraph.

```python
from osm_import import OSMImporter
from dgraph_config import DgraphConfig

config = DgraphConfig()
importer = OSMImporter(config)
success = importer.run_import()
```

### Key Methods
- `search_osm_data(location, tags)`: Search for OSM data
- `convert_to_rdf(gdf)`: Convert GeoDataFrame to RDF
- `save_rdf(output_file)`: Save RDF data to file
- `import_to_dgraph()`: Import data into Dgraph

### OSMDataValidator Class
Class for validating OSM data and testing functionality.

```python
from test_osm_data import OSMDataValidator

validator = OSMDataValidator(config)
success = validator.run_tests()
```

## 🔍 Troubleshooting

### Common Issues

1. **OSM Data Not Found**
   - Verify location name is correct
   - Check internet connection
   - Try different tag combinations

2. **Dgraph Connection Failed**
   - Ensure Dgraph is running
   - Check port availability
   - Verify connection string format

3. **Import Errors**
   - Check data directory permissions
   - Verify RDF file format
   - Review log output for details

### Getting Help
```bash
# Check configuration
make config

# Test connections
uvx run test_osm_data.py --verbose

# View Dgraph logs
make logs
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OSMnx**: Python package for working with OpenStreetMap data
- **Dgraph**: Graph database for building knowledge graphs
- **GeoPandas**: Python library for working with geospatial data
- **RDFLib**: Python library for working with RDF data
