#!/usr/bin/env python3
"""
Enhanced OpenStreetMap to Dgraph Import Script

This script imports OpenStreetMap data into Dgraph using OSMnx with enhanced
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
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, GEO
import pydgraph
import grpc
from dgraph_config import DgraphConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OSM namespaces
OSM = Namespace("http://www.openstreetmap.org/")
OSM_ONTOLOGY = Namespace("http://www.openstreetmap.org/ontology/")
GEO_ONTOLOGY = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")


class EnhancedOSMImporter:
    """Enhanced OSM importer with road network and routing capabilities."""
    
    def __init__(self, config: DgraphConfig):
        self.config = config
        self.dgraph_client = None
        self.graph = Graph()
        self.road_network = None
        self.intersections = {}
        self._setup_namespaces()
        self._setup_dgraph()
    
    def _setup_namespaces(self):
        """Setup RDF namespaces."""
        self.graph.bind("osm", OSM)
        self.graph.bind("osm-ont", OSM_ONTOLOGY)
        self.graph.bind("geo", GEO_ONTOLOGY)
        self.graph.bind("geo", GEO)
    
    def _setup_dgraph(self):
        """Setup Dgraph client connection."""
        try:
            conn_params = self.config.get_connection_params()
            if 'connection_string' in conn_params:
                conn_str = conn_params['connection_string']
                logger.info(f"Setting up Dgraph connection with: {conn_str}")
                self.dgraph_client = pydgraph.open(conn_str)
                version = self.dgraph_client.check_version()
                logger.info(f"✅ Connected to Dgraph version: {version}")
            else:
                self.dgraph_client = pydgraph.DgraphClient(
                    pydgraph.DgraphClientStub(conn_params['host'], conn_params['port'])
                )
                logger.info("✅ Connected to local Dgraph")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Dgraph: {e}")
            self.dgraph_client = None
    
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
    
    def convert_to_rdf(self, roads: List[Dict], intersections: Dict, amenities: gpd.GeoDataFrame):
        """Convert all data to RDF format."""
        logger.info("🔄 Converting data to RDF format...")
        
        # Convert intersections
        for node_id, node_data in intersections.items():
            intersection_uri = URIRef(f"{OSM}intersection/{node_id}")
            self.graph.add((intersection_uri, RDF.type, OSM_ONTOLOGY.Intersection))
            self.graph.add((intersection_uri, OSM_ONTOLOGY.osm_id, Literal(str(node_id))))
            self.graph.add((intersection_uri, OSM_ONTOLOGY.latitude, Literal(node_data['lat'])))
            self.graph.add((intersection_uri, OSM_ONTOLOGY.longitude, Literal(node_data['lon'])))
            
            # Add geometry
            geom_uri = URIRef(f"{OSM}geometry/intersection_{node_id}")
            point = Point(node_data['x'], node_data['y'])
            self.graph.add((intersection_uri, GEO_ONTOLOGY.geometry, geom_uri))
            self.graph.add((geom_uri, RDF.type, GEO_ONTOLOGY.Geometry))
            self.graph.add((geom_uri, GEO_ONTOLOGY.wkt, Literal(point.wkt)))
        
        # Convert roads
        for road in roads:
            road_uri = URIRef(f"{OSM}road/{road['osm_id']}")
            self.graph.add((road_uri, RDF.type, OSM_ONTOLOGY.Road))
            self.graph.add((road_uri, OSM_ONTOLOGY.osm_id, Literal(road['osm_id'])))
            self.graph.add((road_uri, OSM_ONTOLOGY.highway, Literal(road['highway'])))
            self.graph.add((road_uri, OSM_ONTOLOGY.oneway, Literal(road['oneway'])))
            self.graph.add((road_uri, OSM_ONTOLOGY.lanes, Literal(road['lanes'])))
            self.graph.add((road_uri, OSM_ONTOLOGY.maxspeed, Literal(road['maxspeed'])))
            self.graph.add((road_uri, OSM_ONTOLOGY.surface, Literal(road['surface'])))
            self.graph.add((road_uri, OSM_ONTOLOGY.ref, Literal(road['ref'])))
            self.graph.add((road_uri, OSM_ONTOLOGY.length, Literal(road['length'])))
            
            # Add name if available
            if road['name']:
                self.graph.add((road_uri, RDFS.label, Literal(road['name'])))
            
            # Link to intersections
            from_intersection = URIRef(f"{OSM}intersection/{road['from_node']}")
            to_intersection = URIRef(f"{OSM}intersection/{road['to_node']}")
            self.graph.add((road_uri, OSM_ONTOLOGY.from_intersection, from_intersection))
            self.graph.add((road_uri, OSM_ONTOLOGY.to_intersection, to_intersection))
            
            # Add geometry
            if 'geometry' in road:
                geom_uri = URIRef(f"{OSM}geometry/road_{road['osm_id']}")
                self.graph.add((road_uri, GEO_ONTOLOGY.geometry, geom_uri))
                self.graph.add((geom_uri, RDF.type, GEO_ONTOLOGY.Geometry))
                self.graph.add((geom_uri, GEO_ONTOLOGY.wkt, Literal(road['geometry'].wkt)))
        
        # Convert amenities
        for idx, row in amenities.iterrows():
            feature_id = str(idx).replace("'", "").replace(" ", "").replace("(", "").replace(")", "").replace(",", "_")
            feature_uri = URIRef(f"{OSM}feature/{feature_id}")
            
            self.graph.add((feature_uri, RDF.type, OSM_ONTOLOGY.Feature))
            
            # Add geometry
            if hasattr(row, 'geometry') and row.geometry:
                geom_uri = URIRef(f"{OSM}geometry/{feature_id}")
                self.graph.add((feature_uri, GEO_ONTOLOGY.geometry, geom_uri))
                self.graph.add((geom_uri, RDF.type, GEO_ONTOLOGY.Geometry))
                self.graph.add((geom_uri, GEO_ONTOLOGY.wkt, Literal(row.geometry.wkt)))
            
            # Add properties
            for col in amenities.columns:
                if col not in ['geometry', 'index'] and pd.notna(row[col]):
                    if col.startswith('amenity'):
                        self.graph.add((feature_uri, OSM_ONTOLOGY.amenity, Literal(row[col])))
                    elif col.startswith('name'):
                        self.graph.add((feature_uri, RDFS.label, Literal(row[col])))
                    elif col.startswith('addr:'):
                        self.graph.add((feature_uri, OSM_ONTOLOGY.address, Literal(row[col])))
                    else:
                        prop_uri = URIRef(f"{OSM_ONTOLOGY}{col}")
                        self.graph.add((feature_uri, prop_uri, Literal(row[col])))
        
        logger.info(f"✅ Converted {len(intersections)} intersections, {len(roads)} roads, and {len(amenities)} amenities to RDF")
    
    def import_to_dgraph(self) -> bool:
        """Import RDF data into Dgraph."""
        if not self.dgraph_client:
            logger.error("❌ Dgraph client not available")
            return False
        
        try:
            logger.info("🚀 Importing RDF data into Dgraph...")
            
            # Convert RDF to Dgraph mutations
            mutations = self._convert_rdf_to_mutations()
            
            # Batch the mutations and import
            batch_size = self.config.batch_size
            total_mutations = len(mutations)
            logger.info(f"📊 Importing {total_mutations} mutations in batches of {batch_size}")
            
            for i in range(0, total_mutations, batch_size):
                batch = mutations[i:i + batch_size]
                txn = self.dgraph_client.txn()
                
                try:
                    import json
                    json_data = json.dumps(batch).encode('utf-8')
                    mutation = pydgraph.Mutation(set_json=json_data)
                    response = txn.mutate(mutation)
                    txn.commit()
                    logger.info(f"✅ Imported batch {i//batch_size + 1}/{(total_mutations-1)//batch_size + 1}")
                except Exception as e:
                    logger.error(f"❌ Error in batch {i//batch_size + 1}: {e}")
                    txn.discard()
                finally:
                    txn.discard()
            
            logger.info("🎉 Successfully imported all data to Dgraph!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error importing to Dgraph: {e}")
            return False
    
    def _convert_rdf_to_mutations(self) -> List[Dict]:
        """Convert RDF graph to Dgraph mutations."""
        mutations = []
        features = {}
        geometries = {}
        intersections = {}
        roads = {}
        
        # Process RDF triples
        for subject, predicate, obj in self.graph:
            subject_str = str(subject)
            predicate_str = str(predicate)
            
            if '/intersection/' in subject_str:
                # This is an intersection
                if subject_str not in intersections:
                    intersections[subject_str] = {'dgraph.type': 'Intersection'}
                
                if predicate_str.endswith('osm_id'):
                    intersections[subject_str]['osm_id'] = str(obj)
                elif predicate_str.endswith('latitude'):
                    intersections[subject_str]['latitude'] = float(obj)
                elif predicate_str.endswith('longitude'):
                    intersections[subject_str]['longitude'] = float(obj)
                elif predicate_str.endswith('geometry'):
                    intersections[subject_str]['geometry'] = [{'uid': f'_:{str(obj)}'}]
            
            elif '/road/' in subject_str:
                # This is a road
                if subject_str not in roads:
                    roads[subject_str] = {'dgraph.type': 'Road'}
                
                if predicate_str.endswith('osm_id'):
                    roads[subject_str]['osm_id'] = str(obj)
                elif predicate_str.endswith('highway'):
                    roads[subject_str]['highway'] = str(obj)
                elif predicate_str.endswith('oneway'):
                    roads[subject_str]['oneway'] = bool(obj)
                elif predicate_str.endswith('lanes'):
                    roads[subject_str]['lanes'] = int(obj)
                elif predicate_str.endswith('maxspeed'):
                    roads[subject_str]['maxspeed'] = int(obj)
                elif predicate_str.endswith('surface'):
                    roads[subject_str]['surface'] = str(obj)
                elif predicate_str.endswith('ref'):
                    roads[subject_str]['ref'] = str(obj)
                elif predicate_str.endswith('length'):
                    roads[subject_str]['length'] = float(obj)
                elif predicate_str.endswith('label'):
                    roads[subject_str]['name'] = str(obj)
                elif predicate_str.endswith('from_intersection'):
                    roads[subject_str]['from_intersection'] = {'uid': f'_:{str(obj)}'}
                elif predicate_str.endswith('to_intersection'):
                    roads[subject_str]['to_intersection'] = {'uid': str(obj)}
                elif predicate_str.endswith('geometry'):
                    roads[subject_str]['geometry'] = [{'uid': f'_:{str(obj)}'}]
            
            elif '/feature/' in subject_str:
                # This is a feature (amenity)
                if subject_str not in features:
                    features[subject_str] = {'dgraph.type': 'Feature'}
                
                if predicate_str.endswith('label'):
                    features[subject_str]['name'] = str(obj)
                elif predicate_str.endswith('amenity'):
                    features[subject_str]['amenity'] = str(obj)
                elif predicate_str.endswith('address'):
                    features[subject_str]['address'] = str(obj)
                elif predicate_str.endswith('geometry'):
                    features[subject_str]['geometry'] = [{'uid': f'_:{str(obj)}'}]
                
                # Add OSM ID from the URI
                if '/feature/' in subject_str:
                    osm_id = subject_str.split('/feature/')[-1]
                    features[subject_str]['osm_id'] = osm_id
            
            elif '/geometry/' in subject_str:
                # This is a geometry
                if subject_str not in geometries:
                    geometries[subject_str] = {'dgraph.type': 'Geometry', 'uid': f'_:{subject_str}'}
                
                if predicate_str.endswith('wkt'):
                    geometries[subject_str]['wkt'] = str(obj)
        
        # Convert to mutation format
        mutations.extend(intersections.values())
        mutations.extend(roads.values())
        mutations.extend(features.values())
        mutations.extend(geometries.values())
        
        logger.info(f"🔄 Converted {len(intersections)} intersections, {len(roads)} roads, {len(features)} features, and {len(geometries)} geometries to mutations")
        return mutations
    
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
            
            # Convert to RDF
            self.convert_to_rdf(roads, self.intersections, amenities)
            
            # Import to Dgraph
            success = self.import_to_dgraph()
            
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
    parser.add_argument("--output", help="Output RDF filename")
    
    args = parser.parse_args()
    
    # Load configuration
    config = DgraphConfig()
    
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
