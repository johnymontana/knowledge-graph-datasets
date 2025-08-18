#!/usr/bin/env python3
"""
OpenStreetMap to Dgraph Import Script

This script imports OpenStreetMap data into Dgraph using OSMnx.
It searches for OSM data based on location and tags, converts it to RDF format,
and imports it into Dgraph for knowledge graph analysis.
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, List
import osmnx as ox
import geopandas as gpd
import pandas as pd
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


class OSMImporter:
    """Main class for importing OSM data into Dgraph."""
    
    def __init__(self, config: DgraphConfig):
        self.config = config
        self.dgraph_client = None
        self.graph = Graph()
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
                # Use pydgraph.open() with the connection string directly
                conn_str = conn_params['connection_string']
                logger.info(f"Setting up Dgraph connection with: {conn_str}")
                
                self.dgraph_client = pydgraph.open(conn_str)
                
                # Test connection
                version = self.dgraph_client.check_version()
                logger.info(f"✅ Connected to Dgraph version: {version}")
            else:
                # Local connection
                self.dgraph_client = pydgraph.DgraphClient(
                    pydgraph.DgraphClientStub(conn_params['host'], conn_params['port'])
                )
                logger.info("✅ Connected to local Dgraph")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Dgraph: {e}")
            self.dgraph_client = None
    
    def search_osm_data(self, location: str, tags: Dict[str, str]) -> gpd.GeoDataFrame:
        """Search for OSM data using OSMnx."""
        try:
            logger.info(f"🔍 Searching OSM data for location: {location}")
            logger.info(f"🏷️  Tags: {tags}")
            
            # Search for OSM data
            gdf = ox.features_from_place(location, tags=tags)
            
            if gdf.empty:
                logger.warning("⚠️  No OSM data found for the specified location and tags")
                return gdf
            
            logger.info(f"✅ Found {len(gdf)} OSM features")
            return gdf
            
        except Exception as e:
            logger.error(f"❌ Error searching OSM data: {e}")
            return gpd.GeoDataFrame()
    
    def convert_to_rdf(self, gdf: gpd.GeoDataFrame) -> Graph:
        """Convert GeoDataFrame to RDF format."""
        logger.info("🔄 Converting OSM data to RDF format...")
        
        for idx, row in gdf.iterrows():
            # Create URI for the feature - properly handle tuple indices
            feature_id = str(idx).replace("'", "").replace(" ", "").replace("(", "").replace(")", "").replace(",", "_")
            feature_uri = URIRef(f"{OSM}feature/{feature_id}")
            
            # Add basic type information
            self.graph.add((feature_uri, RDF.type, OSM_ONTOLOGY.Feature))
            
            # Add geometry information
            if hasattr(row, 'geometry') and row.geometry:
                geom_uri = URIRef(f"{OSM}geometry/{feature_id}")
                self.graph.add((feature_uri, GEO_ONTOLOGY.geometry, geom_uri))
                self.graph.add((geom_uri, RDF.type, GEO_ONTOLOGY.Geometry))
                
                # Add WKT representation
                wkt_literal = Literal(row.geometry.wkt, datatype=XSD.string)
                self.graph.add((geom_uri, GEO_ONTOLOGY.wkt, wkt_literal))
            
            # Add OSM tags as properties
            for col in gdf.columns:
                if col not in ['geometry', 'index'] and pd.notna(row[col]):
                    if col.startswith('amenity'):
                        self.graph.add((feature_uri, OSM_ONTOLOGY.amenity, Literal(row[col])))
                    elif col.startswith('name'):
                        self.graph.add((feature_uri, RDFS.label, Literal(row[col])))
                    elif col.startswith('addr:'):
                        self.graph.add((feature_uri, OSM_ONTOLOGY.address, Literal(row[col])))
                    else:
                        # Generic property
                        prop_uri = URIRef(f"{OSM_ONTOLOGY}{col}")
                        self.graph.add((feature_uri, prop_uri, Literal(row[col])))
        
        logger.info(f"✅ Converted {len(gdf)} features to RDF")
        return self.graph
    
    def save_rdf(self, output_file: str):
        """Save RDF data to file."""
        try:
            output_path = os.path.join(self.config.data_dir, output_file)
            self.graph.serialize(destination=output_path, format='xml')
            logger.info(f"💾 RDF data saved to: {output_path}")
        except Exception as e:
            logger.error(f"❌ Error saving RDF file: {e}")
    
    def import_to_dgraph(self) -> bool:
        """Import RDF data into Dgraph."""
        if not self.dgraph_client:
            logger.error("❌ Dgraph client not available")
            return False
        
        try:
            logger.info("🚀 Importing RDF data into Dgraph...")
            
            # First, set up the schema
            self._setup_schema()
            
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
                    # Create the mutation with proper JSON encoding
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
    
    def _setup_schema(self):
        """Setup Dgraph schema for OSM data."""
        schema = '''
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
        
        name: string @index(term, fulltext) .
        amenity: string @index(exact, term) .
        address: string @index(term, fulltext) .
        osm_id: string @index(exact) .
        wkt: string .
        geometry: [uid] @reverse .
        '''
        
        try:
            op = pydgraph.Operation(schema=schema)
            self.dgraph_client.alter(op)
            logger.info("✅ Schema updated successfully")
        except Exception as e:
            logger.warning(f"⚠️  Schema update warning: {e}")
    
    def _convert_rdf_to_mutations(self) -> List[Dict]:
        """Convert RDF graph to Dgraph mutations."""
        mutations = []
        features = {}  # Store feature data by URI
        geometries = {}  # Store geometry data by URI
        
        # Process RDF triples
        for subject, predicate, obj in self.graph:
            subject_str = str(subject)
            predicate_str = str(predicate)
            
            if '/feature/' in subject_str:
                # This is a feature
                if subject_str not in features:
                    features[subject_str] = {'dgraph.type': 'Feature'}
                
                if predicate_str.endswith('#label'):
                    features[subject_str]['name'] = str(obj)
                elif predicate_str.endswith('amenity'):
                    features[subject_str]['amenity'] = str(obj)
                elif predicate_str.endswith('address'):
                    features[subject_str]['address'] = str(obj)
                elif predicate_str.endswith('geometry'):
                    # Link to geometry
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
        mutations.extend(features.values())
        mutations.extend(geometries.values())
        
        logger.info(f"🔄 Converted {len(features)} features and {len(geometries)} geometries to mutations")
        return mutations
    
    def run_import(self) -> bool:
        """Run the complete import process."""
        try:
            # Get OSM configuration
            osm_config = self.config.get_osm_config()
            
            # Parse tags properly
            tags = {}
            if '=' in osm_config['tags']:
                key, value = osm_config['tags'].split('=', 1)
                tags[key] = value
            else:
                tags['amenity'] = osm_config['tags']
            
            # Search for OSM data
            gdf = self.search_osm_data(osm_config['location'], tags)
            
            if gdf.empty:
                logger.error("❌ No data to import")
                return False
            
            # Convert to RDF
            self.convert_to_rdf(gdf)
            
            # Save RDF file
            self.save_rdf(osm_config['output_file'])
            
            # Import to Dgraph
            success = self.import_to_dgraph()
            
            if success:
                logger.info("🎉 OSM import completed successfully!")
            else:
                logger.warning("⚠️  Import completed with warnings")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Import failed: {e}")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Import OpenStreetMap data into Dgraph")
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
    importer = OSMImporter(config)
    success = importer.run_import()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
