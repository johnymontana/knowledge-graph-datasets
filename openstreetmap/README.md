# OpenStreetMap to Neo4j Knowledge Graph Project

This project provides a complete solution for importing OpenStreetMap (OSM) data into Neo4j, creating a rich knowledge graph of geographic and amenity information that can be queried and analyzed spatially.

## 🎯 Project Goals

- **Geospatial Data Integration**: Import comprehensive OSM data into Neo4j using OSMnx
- **Knowledge Graph**: Create meaningful relationships between geographic features and amenities
- **Spatial Query Capability**: Enable complex spatial and attribute-based queries
- **Road Network Analysis**: Import complete road networks with intersections for routing
- **Pathfinding & Navigation**: Enable graph-based routing and pathfinding queries
- **Scalability**: Handle large OSM datasets efficiently
- **Ease of Use**: Provide simple tools for setup and data exploration

## 🏗️ Architecture Overview

```
OpenStreetMap Data → OSMnx Python Package → Enhanced Cypher Conversion → Neo4j Database
                                    ↓
                            Road Networks + Intersections + Amenities
                                    ↓
                            Knowledge Graph with Routing Capabilities
```

## 🆕 Enhanced Data Model

The enhanced graph data model now includes:

### **Core Types**
- **`Feature`**: Amenity features (restaurants, shops, etc.)
- **`Geometry`**: Spatial representations (WKT format)
- **`Intersection`**: Road network intersections with coordinates
- **`Road`**: Road segments with properties and connections
- **`Route`**: Pathfinding results between intersections

### **Key Properties**
- **Road Network**: `highway`, `oneway`, `lanes`, `maxspeed`, `surface`, `ref`, `length`
- **Intersections**: `latitude`, `longitude`, `osm_id`, `name`
- **Spatial Data**: `wkt` (Well-Known Text) geometry representations
- **Routing**: `from_intersection`, `to_intersection` relationships

## 🚀 Enhanced Import Process

### **Road Network Import**
The enhanced importer now:
1. **Downloads complete road networks** using OSMnx
2. **Extracts intersections** (nodes) and road segments (edges)
3. **Calculates distances and travel times** for routing
4. **Preserves spatial relationships** between network elements
5. **Imports amenities** with spatial context

### **Data Volume**
- **Road Network**: 9,988 intersections, 27,543 road segments
- **Amenities**: 1,871+ restaurants and other features
- **Spatial Coverage**: Complete San Francisco road network

## 📊 Enhanced Schema

```cypher
// Node Labels and Properties
(:Feature {
    name: string,
    amenity: string,
    address: string,
    osm_id: string,
    highway: string,
    oneway: boolean,
    lanes: integer,
    maxspeed: integer,
    surface: string,
    ref: string
})

(:Geometry {
    geom_id: string,
    wkt: string
})

(:Intersection {
    osm_id: string,
    name: string,
    latitude: float,
    longitude: float
})

(:Road {
    osm_id: string,
    name: string,
    highway: string,
    oneway: boolean,
    lanes: integer,
    maxspeed: integer,
    surface: string,
    ref: string,
    length: float
})

// Relationships
(:Feature|:Intersection|:Road)-[:HAS_GEOMETRY]->(:Geometry)
(:Road)-[:FROM_INTERSECTION]->(:Intersection)
(:Road)-[:TO_INTERSECTION]->(:Intersection)
```

## 🔍 Enhanced Query Examples

### **1. Road Network Analysis**

#### Find all major highways:
```cypher
MATCH (r:Road)-[:FROM_INTERSECTION]->(from_i:Intersection),
      (r)-[:TO_INTERSECTION]->(to_i:Intersection)
WHERE r.highway = 'primary'
RETURN r.name, r.highway, r.length, 
       from_i.latitude, from_i.longitude,
       to_i.latitude, to_i.longitude
LIMIT 100
```

#### Find intersections with high connectivity:
```cypher
MATCH (i:Intersection)<-[:FROM_INTERSECTION]-(r:Road)
WITH i, count(r) as road_count
WHERE road_count > 5
RETURN i.osm_id, i.latitude, i.longitude, road_count
ORDER BY road_count DESC
LIMIT 10
```

### **2. Spatial Routing Queries**

#### Find roads within a specific area:
```cypher
MATCH (r:Road)-[:FROM_INTERSECTION]->(from_i:Intersection),
      (r)-[:TO_INTERSECTION]->(to_i:Intersection)
WHERE from_i.latitude >= 37.78 AND from_i.latitude <= 37.79
  AND from_i.longitude >= -122.4 AND from_i.longitude <= -122.39
RETURN r.name, r.highway, r.length,
       from_i.latitude, from_i.longitude,
       to_i.latitude, to_i.longitude
LIMIT 100
```

#### Find nearest intersection to coordinates:
```cypher
MATCH (i:Intersection)
WITH i, point.distance(
  point({latitude: i.latitude, longitude: i.longitude}),
  point({latitude: 37.7749, longitude: -122.4194})
) AS distance
WHERE distance < 1000
RETURN i.osm_id, i.name, i.latitude, i.longitude, distance
ORDER BY distance
LIMIT 10
```

### **3. Pathfinding & Navigation**

#### Find shortest path between two intersections:
```cypher
MATCH (start:Intersection {osm_id: "123456"}),
      (end:Intersection {osm_id: "789012"})
CALL apoc.algo.dijkstra(start, end, 'FROM_INTERSECTION|TO_INTERSECTION', 'length')
YIELD path, weight
RETURN path, weight
```

#### Analyze road network connectivity:
```cypher
MATCH (r:Road)
RETURN r.highway as road_type,
       count(r) as road_count,
       avg(r.length) as avg_length,
       sum(r.length) as total_length
ORDER BY road_count DESC
```

### **4. Enhanced Amenity Queries**

#### Find restaurants near specific coordinates:
```cypher
MATCH (f:Feature)-[:HAS_GEOMETRY]->(g:Geometry)
WHERE f.amenity = 'restaurant'
  AND g.wkt IS NOT NULL
WITH f, g,
     point.distance(
       point({latitude: 37.7749, longitude: -122.4194}),
       point({latitude: toFloat(split(replace(g.wkt, 'POINT(', ''), ')')[1]), 
              longitude: toFloat(split(replace(g.wkt, 'POINT(', ''), ')')[0])})
     ) as distance
WHERE distance < 500
RETURN f.name, f.amenity, f.address, g.wkt, distance
ORDER BY distance
LIMIT 20
```

#### Find amenities along major roads:
```cypher
MATCH (r:Road)-[:FROM_INTERSECTION]->(i:Intersection)
WHERE r.highway = 'primary'
WITH collect(DISTINCT i) as major_intersections
MATCH (f:Feature)-[:HAS_GEOMETRY]->(g:Geometry)
WHERE f.amenity IS NOT NULL
RETURN f.name, f.amenity, r.name as road_name, r.highway
LIMIT 50
```

## 🛠️ Enhanced Import Script

### **New Features**
- **`osm_import_enhanced.py`**: Enhanced importer with road network support
- **Road Network Extraction**: Downloads and processes complete road networks
- **Intersection Analysis**: Identifies and maps all road intersections
- **Spatial Relationships**: Preserves network topology and connectivity
- **Performance Optimization**: Efficient batch processing for large datasets

### **Usage**
```bash
# Import road network + amenities
uv run python osm_import_enhanced.py \
  --location "San Francisco, California" \
  --tags "amenity=restaurant"
```

## 📈 Performance & Scalability

### **Data Processing**
- **Road Networks**: Handles networks with 10,000+ intersections
- **Batch Processing**: Configurable batch sizes for optimal performance
- **Memory Efficiency**: Streams large datasets without memory issues
- **Parallel Processing**: Future support for concurrent imports

### **Query Performance**
- **Spatial Indexing**: Optimized for geographic queries
- **Graph Traversal**: Efficient pathfinding and routing
- **Aggregation**: Fast statistical analysis of network properties

## 🔮 Future Enhancements

### **Planned Features**
- **Real-time Routing**: Dynamic pathfinding with traffic data
- **Multi-modal Transport**: Support for walking, cycling, and transit
- **Temporal Analysis**: Time-based routing and accessibility
- **Advanced Analytics**: Network centrality, connectivity analysis
- **Integration APIs**: REST endpoints for external applications

### **Advanced Queries**
- **Shortest Path**: Dijkstra and A* algorithm implementations
- **Network Analysis**: Betweenness centrality, clustering coefficients
- **Accessibility**: Isochrone maps and reachability analysis
- **Traffic Flow**: Congestion modeling and optimization

## 📚 Additional Resources

### **Documentation**
- [OSMnx Documentation](https://osmnx.readthedocs.io/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j APOC Procedures](https://neo4j.com/labs/apoc/)
- [OpenStreetMap Data](https://wiki.openstreetmap.org/wiki/Data)

### **Example Datasets**
- **San Francisco**: Complete road network + amenities
- **Restaurant Data**: 1,871+ locations with spatial data
- **Road Properties**: Highway types, speeds, surfaces, lanes

### **Query Templates**
- **Routing**: Pathfinding between any two points
- **Spatial**: Geographic proximity and containment
- **Network**: Connectivity and topology analysis
- **Analytics**: Statistical summaries and aggregations

---

## 🚀 Getting Started

### **Prerequisites**
- Python 3.8+
- Docker and Docker Compose
- uv (Python package manager)

### **Quick Start**

1. **Start Neo4j**:
   ```bash
   ./start_neo4j.sh
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Import OSM data**:
   ```bash
   uv run python osm_import_enhanced.py --location "San Francisco, California" --tags "amenity=restaurant"
   ```

4. **Run sample queries**:
   ```bash
   uv run python sample_queries.py --all
   ```

5. **Access Neo4j Browser**:
   Open http://localhost:7474/browser/ (username: neo4j, password: password)

---

**🎉 The enhanced OpenStreetMap to Neo4j project now provides a complete solution for spatial knowledge graphs with routing capabilities!**
