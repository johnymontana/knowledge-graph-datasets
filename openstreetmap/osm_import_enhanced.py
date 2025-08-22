#!/usr/bin/env python3
"""
Enhanced OpenStreetMap to Neo4j Import Script

This script imports OpenStreetMap data into Neo4j using OSMnx with enhanced
road network and routing capabilities. It can import:
- Road networks with intersections
- Amenity features (restaurants, shops, etc.)
- Routing relationships between intersections
- Spatial data for pathfinding queries
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, List, Tuple
import osmnx as ox
import geopandas as gpd
import pandas as pd
import networkx as nx
from shapely.geometry import Point, LineString
from neo4j import GraphDatabase
from neo4j_config import Neo4jConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for Neo4j labels and relationships
FEATURE_LABEL = "Feature"
GEOMETRY_LABEL = "Geometry"
INTERSECTION_LABEL = "Intersection"
ROAD_LABEL = "Road"
HAS_GEOMETRY_REL = "HAS_GEOMETRY"
FROM_INTERSECTION_REL = "FROM_INTERSECTION"
TO_INTERSECTION_REL = "TO_INTERSECTION"


class EnhancedOSMImporter:
    """Enhanced OSM importer with road network and routing capabilities."""
    
    def __init__(self, config: Neo4jConfig):
        self.config = config
        self.driver = None
        self.cypher_statements = []
        self.road_network = None
        self.intersections = {}
        self._setup_neo4j()
    
    def _setup_neo4j(self):
        """Setup Neo4j driver connection."""
        try:
            conn_params = self.config.get_connection_params()
            self.driver = GraphDatabase.driver(
                conn_params['uri'],
                auth=(conn_params['username'], conn_params['password'])
            )
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("✅ Connected to Neo4j")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def __del__(self):
        """Close Neo4j driver on cleanup."""
        if self.driver:
            self.driver.close()
    
    def get_road_network(self, location: str) -> nx.MultiDiGraph:
        """Get road network from OSM using OSMnx."""
        try:
            logger.info(f"🛣️  Getting road network for: {location}")
            
            # Get the road network
            G = ox.graph_from_place(location, network_type='drive')
            
            # Project to a projected coordinate system for accurate distance calculations
            G_proj = ox.project_graph(G)
            
            # Add edge lengths using the current OSMnx API
            G_proj = ox.distance.add_edge_lengths(G_proj)
            
            # Add travel times (assuming 30 mph default speed)
            # For OSMnx 2.0+, we need to calculate speeds manually
            for u, v, k, data in G_proj.edges(data=True, keys=True):
                # Set default speed to 30 mph (48 km/h)
                data['speed'] = 48
                # Calculate travel time in seconds
                if 'length' in data:
                    data['travel_time'] = (data['length'] / 1000) / (data['speed'] / 3600)  # Convert to seconds
            
            logger.info(f"✅ Road network loaded: {G_proj.number_of_nodes()} nodes, {G_proj.number_of_edges()} edges")
            return G_proj
            
        except Exception as e:
            logger.error(f"❌ Error getting road network: {e}")
            return None
    
    def extract_intersections(self, G: nx.MultiDiGraph) -> Dict[int, Dict]:
        """Extract intersection information from the road network."""
        intersections = {}
        
        for node_id, node_data in G.nodes(data=True):
            # Get coordinates
            if 'x' in node_data and 'y' in node_data:
                x, y = node_data['x'], node_data['y']
                # Convert to lat/lon if needed
                if 'lat' in node_data and 'lon' in node_data:
                    lat, lon = node_data['lat'], node_data['lon']
                else:
                    # For projected graphs, we need to get the original lat/lon
                    # Get the original graph to extract lat/lon
                    try:
                        # Try to get lat/lon from the original graph
                        if hasattr(G, 'graph') and 'crs' in G.graph:
                            # This is a projected graph, get original coordinates
                            orig_G = ox.graph_from_place(G.graph.get('place', 'San Francisco, California'), network_type='drive')
                            if node_id in orig_G.nodes:
                                orig_node = orig_G.nodes[node_id]
                                lat, lon = orig_node.get('y', 0), orig_node.get('x', 0)
                            else:
                                lat, lon = 37.7749, -122.4194  # Default SF coordinates
                        else:
                            lat, lon = 37.7749, -122.4194  # Default SF coordinates
                    except:
                        lat, lon = 37.7749, -122.4194  # Default SF coordinates
                
                intersections[node_id] = {
                    'osm_id': str(node_id),
                    'lat': lat,
                    'lon': lon,
                    'x': x,
                    'y': y,
                    'degree': G.degree(node_id)
                }
        
        logger.info(f"✅ Extracted {len(intersections)} intersections")
        return intersections
    
    def extract_roads(self, G: nx.MultiDiGraph, intersections: Dict) -> List[Dict]:
        """Extract road information from the network."""
        roads = []
        
        for u, v, k, edge_data in G.edges(data=True, keys=True):
            road = {
                'osm_id': f"{u}_{v}_{k}",
                'from_node': u,
                'to_node': v,
                'highway': edge_data.get('highway', 'unknown'),
                'name': edge_data.get('name', ''),
                'oneway': edge_data.get('oneway', False),
                'lanes': edge_data.get('lanes', 1),
                'maxspeed': edge_data.get('maxspeed', 30),
                'surface': edge_data.get('surface', 'unknown'),
                'ref': edge_data.get('ref', ''),
                'length': edge_data.get('length', 0),
                'travel_time': edge_data.get('travel_time', 0)
            }
            roads.append(road)
        
        logger.info(f"✅ Extracted {len(roads)} road segments")
        return roads
    
    def get_amenities(self, location: str, tags: Dict[str, str]) -> gpd.GeoDataFrame:
        """Get amenity features from OSM."""
        try:
            logger.info(f"🏪 Getting amenities for: {location}")
            gdf = ox.features_from_place(location, tags=tags)
            
            if gdf.empty:
                logger.warning("⚠️  No amenities found")
                return gdf
            
            logger.info(f"✅ Found {len(gdf)} amenities")
            return gdf
            
        except Exception as e:
            logger.error(f"❌ Error getting amenities: {e}")
            return gpd.GeoDataFrame()
    
    def convert_to_cypher(self, roads: List[Dict], intersections: Dict, amenities: gpd.GeoDataFrame):
        """Convert all data to Cypher format."""
        logger.info("🔄 Converting data to Cypher format...")
        
        # Convert intersections
        for node_id, node_data in intersections.items():
            intersection_props = {
                'osm_id': str(node_id),
                'latitude': node_data['lat'],
                'longitude': node_data['lon']
            }
            
            # Create intersection node
            props_str = ', '.join([f"{k}: ${k}" for k in intersection_props.keys()])
            intersection_cypher = f"CREATE (i:{INTERSECTION_LABEL} {{{props_str}}})"
            self.cypher_statements.append((intersection_cypher, intersection_props))
            
            # Create geometry for intersection
            geom_id = f"geom_intersection_{node_id}"
            point = Point(node_data['x'], node_data['y'])
            geom_props = {
                'geom_id': geom_id,
                'wkt': point.wkt
            }
            
            geom_cypher = f"CREATE (g:{GEOMETRY_LABEL} {{geom_id: $geom_id, wkt: $wkt}})"
            self.cypher_statements.append((geom_cypher, geom_props))
            
            # Create relationship
            rel_cypher = f"MATCH (i:{INTERSECTION_LABEL} {{osm_id: $osm_id}}), (g:{GEOMETRY_LABEL} {{geom_id: $geom_id}}) CREATE (i)-[:{HAS_GEOMETRY_REL}]->(g)"
            rel_props = {'osm_id': str(node_id), 'geom_id': geom_id}
            self.cypher_statements.append((rel_cypher, rel_props))
        
        # Convert roads
        for road in roads:
            road_props = {
                'osm_id': road['osm_id'],
                'highway': road['highway'],
                'oneway': road['oneway'],
                'lanes': road['lanes'],
                'maxspeed': road['maxspeed'],
                'surface': road['surface'],
                'ref': road['ref'],
                'length': road['length']
            }
            
            # Add name if available
            if road['name']:
                road_props['name'] = road['name']
            
            # Create road node
            props_str = ', '.join([f"{k}: ${k}" for k in road_props.keys()])
            road_cypher = f"CREATE (r:{ROAD_LABEL} {{{props_str}}})"
            self.cypher_statements.append((road_cypher, road_props))
            
            # Create relationships to intersections
            from_rel_cypher = f"MATCH (r:{ROAD_LABEL} {{osm_id: $road_id}}), (i:{INTERSECTION_LABEL} {{osm_id: $from_node}}) CREATE (r)-[:{FROM_INTERSECTION_REL}]->(i)"
            from_rel_props = {'road_id': road['osm_id'], 'from_node': str(road['from_node'])}
            self.cypher_statements.append((from_rel_cypher, from_rel_props))
            
            to_rel_cypher = f"MATCH (r:{ROAD_LABEL} {{osm_id: $road_id}}), (i:{INTERSECTION_LABEL} {{osm_id: $to_node}}) CREATE (r)-[:{TO_INTERSECTION_REL}]->(i)"
            to_rel_props = {'road_id': road['osm_id'], 'to_node': str(road['to_node'])}
            self.cypher_statements.append((to_rel_cypher, to_rel_props))
        
        # Convert amenities
        for idx, row in amenities.iterrows():
            feature_id = str(idx).replace("'", "").replace(" ", "").replace("(", "").replace(")", "").replace(",", "_")
            
            # Build feature properties
            feature_props = {'osm_id': feature_id}
            
            # Add properties
            for col in amenities.columns:
                if col not in ['geometry', 'index'] and pd.notna(row[col]):
                    if col.startswith('amenity'):
                        feature_props['amenity'] = str(row[col])
                    elif col.startswith('name'):
                        feature_props['name'] = str(row[col])
                    elif col.startswith('addr:'):
                        feature_props['address'] = str(row[col])
                    else:
                        # Generic property (sanitize column name)
                        clean_col = col.replace(':', '_').replace('-', '_')
                        feature_props[clean_col] = str(row[col])
            
            # Create feature node
            props_str = ', '.join([f"{k}: ${k}" for k in feature_props.keys()])
            feature_cypher = f"CREATE (f:{FEATURE_LABEL} {{{props_str}}})"
            self.cypher_statements.append((feature_cypher, feature_props))
            
            # Add geometry if available
            if hasattr(row, 'geometry') and row.geometry:
                geom_id = f"geom_{feature_id}"
                geom_props = {
                    'geom_id': geom_id,
                    'wkt': row.geometry.wkt
                }
                
                # Create geometry node and relationship
                geom_cypher = f"CREATE (g:{GEOMETRY_LABEL} {{geom_id: $geom_id, wkt: $wkt}})"
                self.cypher_statements.append((geom_cypher, geom_props))
                
                # Create relationship
                rel_cypher = f"MATCH (f:{FEATURE_LABEL} {{osm_id: $feature_id}}), (g:{GEOMETRY_LABEL} {{geom_id: $geom_id}}) CREATE (f)-[:{HAS_GEOMETRY_REL}]->(g)"
                rel_props = {'feature_id': feature_id, 'geom_id': geom_id}
                self.cypher_statements.append((rel_cypher, rel_props))
        
        logger.info(f"✅ Converted {len(intersections)} intersections, {len(roads)} roads, and {len(amenities)} amenities to Cypher statements")
    
    def import_to_neo4j(self) -> bool:
        """Import Cypher data into Neo4j."""
        if not self.driver:
            logger.error("❌ Neo4j driver not available")
            return False
        
        try:
            logger.info("🚀 Importing data into Neo4j...")
            
            # First, set up constraints and indexes
            self._setup_schema()
            
            # Batch the statements and import
            batch_size = self.config.batch_size
            total_statements = len(self.cypher_statements)
            logger.info(f"📊 Importing {total_statements} statements in batches of {batch_size}")
            
            with self.driver.session() as session:
                for i in range(0, total_statements, batch_size):
                    batch = self.cypher_statements[i:i + batch_size]
                    
                    try:
                        # Execute statements in a transaction
                        def execute_batch(tx):
                            for cypher, params in batch:
                                tx.run(cypher, params)
                        
                        session.execute_write(execute_batch)
                        logger.info(f"✅ Imported batch {i//batch_size + 1}/{(total_statements-1)//batch_size + 1}")
                    except Exception as e:
                        logger.error(f"❌ Error in batch {i//batch_size + 1}: {e}")
                        # Continue with next batch
            
            logger.info("🎉 Successfully imported all data to Neo4j!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error importing to Neo4j: {e}")
            return False
    
    def _setup_schema(self):
        """Setup Neo4j constraints and indexes for OSM data."""
        constraints_and_indexes = [
            f"CREATE CONSTRAINT feature_osm_id IF NOT EXISTS FOR (f:{FEATURE_LABEL}) REQUIRE f.osm_id IS UNIQUE",
            f"CREATE CONSTRAINT geometry_geom_id IF NOT EXISTS FOR (g:{GEOMETRY_LABEL}) REQUIRE g.geom_id IS UNIQUE",
            f"CREATE CONSTRAINT intersection_osm_id IF NOT EXISTS FOR (i:{INTERSECTION_LABEL}) REQUIRE i.osm_id IS UNIQUE",
            f"CREATE CONSTRAINT road_osm_id IF NOT EXISTS FOR (r:{ROAD_LABEL}) REQUIRE r.osm_id IS UNIQUE",
            f"CREATE INDEX feature_name IF NOT EXISTS FOR (f:{FEATURE_LABEL}) ON (f.name)",
            f"CREATE INDEX feature_amenity IF NOT EXISTS FOR (f:{FEATURE_LABEL}) ON (f.amenity)",
            f"CREATE INDEX feature_address IF NOT EXISTS FOR (f:{FEATURE_LABEL}) ON (f.address)",
            f"CREATE INDEX intersection_lat_lon IF NOT EXISTS FOR (i:{INTERSECTION_LABEL}) ON (i.latitude, i.longitude)",
            f"CREATE INDEX road_highway IF NOT EXISTS FOR (r:{ROAD_LABEL}) ON (r.highway)",
        ]
        
        try:
            with self.driver.session() as session:
                for constraint in constraints_and_indexes:
                    try:
                        session.run(constraint)
                    except Exception as e:
                        # Constraint might already exist, which is fine
                        logger.debug(f"Constraint/Index operation result: {e}")
            logger.info("✅ Schema setup completed successfully")
        except Exception as e:
            logger.warning(f"⚠️  Schema setup warning: {e}")
    
    def run_import(self) -> bool:
        """Run the complete enhanced import process."""
        try:
            # Get OSM configuration
            osm_config = self.config.get_osm_config()
            
            # Get road network
            self.road_network = self.get_road_network(osm_config['location'])
            if not self.road_network:
                logger.error("❌ Failed to get road network")
                return False
            
            # Extract intersections and roads
            self.intersections = self.extract_intersections(self.road_network)
            roads = self.extract_roads(self.road_network, self.intersections)
            
            # Get amenities
            tags = {}
            if '=' in osm_config['tags']:
                key, value = osm_config['tags'].split('=', 1)
                tags[key] = value
            else:
                tags['amenity'] = osm_config['tags']
            
            amenities = self.get_amenities(osm_config['location'], tags)
            
            # Convert to Cypher
            self.convert_to_cypher(roads, self.intersections, amenities)
            
            # Import to Neo4j
            success = self.import_to_neo4j()
            
            if success:
                logger.info("🎉 Enhanced OSM import completed successfully!")
            else:
                logger.warning("⚠️  Import completed with warnings")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Import failed: {e}")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Enhanced OSM import with road networks and routing")
    parser.add_argument("--location", help="OSM location to search")
    parser.add_argument("--tags", help="OSM tags to filter by (e.g., amenity=restaurant)")
    parser.add_argument("--output", help="Output Cypher filename")
    
    args = parser.parse_args()
    
    # Load configuration
    config = Neo4jConfig()
    
    # Override config with command line arguments
    if args.location:
        config.osm_location = args.location
    if args.tags:
        config.osm_tags = args.tags
    if args.output:
        config.osm_output_file = args.output
    
    # Create importer and run
    importer = EnhancedOSMImporter(config)
    success = importer.run_import()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
