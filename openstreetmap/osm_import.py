#!/usr/bin/env python3
"""
OpenStreetMap to Neo4j Import Script

This script imports OpenStreetMap data into Neo4j using OSMnx.
It searches for OSM data based on location and tags, converts it to Cypher format,
and imports it into Neo4j for knowledge graph analysis.
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, List
import osmnx as ox
import geopandas as gpd
import pandas as pd
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
HAS_GEOMETRY_REL = "HAS_GEOMETRY"


class OSMImporter:
    """Main class for importing OSM data into Neo4j."""
    
    def __init__(self, config: Neo4jConfig):
        self.config = config
        self.driver = None
        self.cypher_statements = []
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
    
    def convert_to_cypher(self, gdf: gpd.GeoDataFrame):
        """Convert GeoDataFrame to Cypher statements."""
        logger.info("🔄 Converting OSM data to Cypher format...")
        
        for idx, row in gdf.iterrows():
            # Create unique feature ID - properly handle tuple indices
            feature_id = str(idx).replace("'", "").replace(" ", "").replace("(", "").replace(")", "").replace(",", "_")
            
            # Build feature properties
            feature_props = {'osm_id': feature_id}
            
            # Add OSM tags as properties
            for col in gdf.columns:
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
            
            # Create Cypher statement for feature
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
        
        logger.info(f"✅ Converted {len(gdf)} features to Cypher statements")
    
    def save_cypher(self, output_file: str):
        """Save Cypher statements to file."""
        try:
            output_path = os.path.join(self.config.data_dir, output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                for cypher, params in self.cypher_statements:
                    # Write the Cypher statement with parameters as comments
                    f.write(f"// Parameters: {params}\n")
                    f.write(f"{cypher};\n\n")
            logger.info(f"💾 Cypher data saved to: {output_path}")
        except Exception as e:
            logger.error(f"❌ Error saving Cypher file: {e}")
    
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
            f"CREATE INDEX feature_name IF NOT EXISTS FOR (f:{FEATURE_LABEL}) ON (f.name)",
            f"CREATE INDEX feature_amenity IF NOT EXISTS FOR (f:{FEATURE_LABEL}) ON (f.amenity)",
            f"CREATE INDEX feature_address IF NOT EXISTS FOR (f:{FEATURE_LABEL}) ON (f.address)",
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
    
    # Note: This method is no longer needed since we directly generate Cypher statements
    # in the convert_to_cypher method
    
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
            
            # Convert to Cypher
            self.convert_to_cypher(gdf)
            
            # Save Cypher file
            self.save_cypher(osm_config['output_file'])
            
            # Import to Neo4j
            success = self.import_to_neo4j()
            
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
    parser = argparse.ArgumentParser(description="Import OpenStreetMap data into Neo4j")
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
    importer = OSMImporter(config)
    success = importer.run_import()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
