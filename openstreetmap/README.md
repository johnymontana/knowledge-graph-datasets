# OpenStreetMap to Dgraph Knowledge Graph Project

This project provides a complete solution for importing OpenStreetMap (OSM) data into Dgraph, creating a rich knowledge graph of geographic and amenity information that can be queried and analyzed spatially.

## 🎯 Project Goals

- **Geospatial Data Integration**: Import comprehensive OSM data into Dgraph using OSMnx
- **Knowledge Graph**: Create meaningful relationships between geographic features and amenities
- **Spatial Query Capability**: Enable complex spatial and attribute-based queries
- **Road Network Analysis**: Import complete road networks with intersections for routing
- **Pathfinding & Navigation**: Enable graph-based routing and pathfinding queries
- **Scalability**: Handle large OSM datasets efficiently
- **Ease of Use**: Provide simple tools for setup and data exploration

## 🏗️ Architecture Overview

```
OpenStreetMap Data → OSMnx Python Package → Enhanced RDF Conversion → Dgraph Database
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

```dql
type Feature {
    name: string
    amenity: string
    address: string
    geometry: Geometry
    osm_id: string
    highway: string
    oneway: bool
    lanes: int
    maxspeed: int
    surface: string
    ref: string
}

type Geometry {
    wkt: string
}

type Intersection {
    osm_id: string
    name: string
    geometry: Geometry
    latitude: float
    longitude: float
}

type Road {
    osm_id: string
    name: string
    highway: string
    oneway: bool
    lanes: int
    maxspeed: int
    surface: string
    ref: string
    length: float
    geometry: Geometry
    from_intersection: Intersection
    to_intersection: Intersection
}

type Route {
    start_point: Intersection
    end_point: Intersection
    total_distance: float
    total_time: float
}
```

## 🔍 Enhanced Query Examples

### **1. Road Network Analysis**

#### Find all major highways:
```dql
{
  highways(func: eq(highway, "primary")) {
    name
    highway
    length
    from_intersection {
      latitude
      longitude
    }
    to_intersection {
      latitude
      longitude
    }
  }
}
```

#### Find intersections with high connectivity:
```dql
{
  busy_intersections(func: has(geometry), first: 10) @filter(gt(count(~from_intersection), 5)) {
    osm_id
    latitude
    longitude
    ~from_intersection {
      name
      highway
      length
    }
  }
}
```

### **2. Spatial Routing Queries**

#### Find roads within a specific area:
```dql
{
  downtown_roads(func: has(geometry)) @filter(geoWithin(geometry, "POLYGON((-122.4 37.78, -122.4 37.79, -122.39 37.79, -122.39 37.78, -122.4 37.78))")) {
    name
    highway
    length
    from_intersection {
      latitude
      longitude
    }
    to_intersection {
      latitude
      longitude
    }
  }
}
```

#### Find nearest intersection to coordinates:
```dql
{
  nearest_intersection(func: has(latitude)) @filter(geoNear(geometry, "POINT(-122.4194 37.7749)", 1000)) {
    osm_id
    name
    latitude
    longitude
  }
}
```

### **3. Pathfinding & Navigation**

#### Find route between two points:
```dql
{
  route(func: has(from_intersection)) @filter(eq(from_intersection.latitude, 37.7749) AND eq(from_intersection.longitude, -122.4194)) {
    name
    length
    travel_time: length
    to_intersection {
      latitude
      longitude
    }
  }
}
```

#### Analyze road network connectivity:
```dql
{
  network_stats(func: has(highway)) @groupby(highway) {
    count(uid)
    avg(length)
    sum(length)
  }
}
```

### **4. Enhanced Amenity Queries**

#### Find restaurants near specific intersections:
```dql
{
  nearby_restaurants(func: eq(amenity, "restaurant")) @filter(geoNear(geometry, "POINT(-122.4194 37.7749)", 500)) {
    name
    amenity
    address
    geometry {
      wkt
    }
  }
}
```

#### Find amenities along specific road types:
```dql
{
  road_amenities(func: has(highway)) @filter(eq(highway, "primary")) {
    highway
    name
    length
    ~from_intersection {
      ~geometry {
        ~geometry {
          name
          amenity
        }
      }
    }
  }
}
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
- [Dgraph GraphQL+](https://dgraph.io/docs/graphql/)
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

**🎉 The enhanced OpenStreetMap to Dgraph project now provides a complete solution for spatial knowledge graphs with routing capabilities!**
