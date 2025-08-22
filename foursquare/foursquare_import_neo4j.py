#!/usr/bin/env python3
"""
Foursquare to Neo4j Import Script

This script imports Foursquare transit stops and places data into Neo4j,
creating a knowledge graph with geospatial capabilities for routing and proximity analysis.

Requirements:
- Python 3.7+
- neo4j library
- pandas library

Usage:
    python foursquare_import_neo4j.py [--config-file CONFIG_FILE] [--data-dir DATA_DIR]
"""

import csv
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
from neo4j import GraphDatabase
import pandas as pd

# Add parent directory to path to import neo4j_config
sys.path.append(str(Path(__file__).parent.parent / 'gtfs'))
from neo4j_config import Neo4jConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FoursquareImporter:
    """Imports Foursquare transit and places data into Neo4j"""
    
    def __init__(self, config: Neo4jConfig = None, data_dir: str = None, batch_size: int = None):
        # Load configuration
        if config is None:
            config = Neo4jConfig()
        
        self.config = config
        self.data_dir = Path(data_dir or os.getenv('DATA_DIR', 'data'))
        
        # Create Neo4j driver
        self.driver = self._create_neo4j_driver()
        
        # Batch size for mutations
        self.batch_size = batch_size or int(os.getenv('BATCH_SIZE', '1000'))
        
        # Track imported entities
        self.imported_count = {
            'transit_stops': 0,
            'places': 0,
            'categories': 0,
            'relationships': 0
        }
    
    def _create_neo4j_driver(self):
        """Create and configure Neo4j driver"""
        try:
            driver = GraphDatabase.driver(
                self.config.uri,
                auth=self.config.get_auth(),
                **self.config.get_driver_config()
            )
            logger.info("Successfully created Neo4j driver")
            return driver
        except Exception as e:
            logger.error(f"Failed to create Neo4j driver: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test connection to Neo4j"""
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    logger.info("Successfully connected to Neo4j")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False
    
    def create_schema(self) -> bool:
        """Create the Neo4j schema for Foursquare data"""
        logger.info("Creating Neo4j schema for Foursquare data...")
        
        try:
            with self.driver.session(database=self.config.database) as session:
                # Create constraints for unique identifiers
                constraints = [
                    "CREATE CONSTRAINT transit_stop_id_unique IF NOT EXISTS FOR (ts:TransitStop) REQUIRE ts.stop_id IS UNIQUE",
                    "CREATE CONSTRAINT place_id_unique IF NOT EXISTS FOR (p:Place) REQUIRE p.fsq_place_id IS UNIQUE",
                    "CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.category_id IS UNIQUE"
                ]
                
                for constraint in constraints:
                    try:
                        session.run(constraint)
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            logger.warning(f"Constraint creation failed: {constraint} - {e}")
                
                # Create geospatial indexes
                indexes = [
                    "CREATE INDEX transit_stop_location IF NOT EXISTS FOR (ts:TransitStop) ON (ts.stop_lat, ts.stop_lon)",
                    "CREATE INDEX place_location IF NOT EXISTS FOR (p:Place) ON (p.latitude, p.longitude)",
                    "CREATE INDEX place_name IF NOT EXISTS FOR (p:Place) ON p.name",
                    "CREATE INDEX category_label IF NOT EXISTS FOR (c:Category) ON c.label",
                    "CREATE INDEX place_locality IF NOT EXISTS FOR (p:Place) ON p.locality",
                    "CREATE INDEX place_region IF NOT EXISTS FOR (p:Place) ON p.region"
                ]
                
                for index in indexes:
                    try:
                        session.run(index)
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            logger.warning(f"Index creation failed: {index} - {e}")
                
                # Create Point indexes for spatial queries (if supported)
                try:
                    session.run("""
                        CREATE INDEX transit_stop_point IF NOT EXISTS 
                        FOR (ts:TransitStop) ON (ts.location)
                    """)
                    session.run("""
                        CREATE INDEX place_point IF NOT EXISTS 
                        FOR (p:Place) ON (p.location)
                    """)
                except Exception as e:
                    logger.warning(f"Point index creation failed: {e}")
            
            logger.info("Successfully created Neo4j schema")
            return True
        except Exception as e:
            logger.error(f"Error creating schema: {e}")
            return False
    
    def read_csv_file(self, filename: str) -> List[Dict[str, Any]]:
        """Read a CSV file and return list of dictionaries"""
        filepath = self.data_dir / filename
        if not filepath.exists():
            logger.warning(f"File {filename} not found at {filepath}")
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            logger.error(f"Error reading {filename}: {e}")
            return []
    
    def convert_transit_stops_to_neo4j(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert transit stops CSV data to Neo4j format"""
        neo4j_data = []
        
        for row in data:
            cleaned_row = {}
            
            for key, value in row.items():
                if value == '' or value is None:
                    continue
                
                # Convert coordinates to float
                if key in ['stop_lat', 'stop_lon']:
                    try:
                        cleaned_row[key] = float(value)
                    except (ValueError, TypeError):
                        continue
                
                # Convert integer fields
                elif key in ['location_type', 'wheelchair_boarding']:
                    try:
                        cleaned_row[key] = int(float(value))
                    except (ValueError, TypeError):
                        continue
                
                # Keep string fields
                else:
                    cleaned_row[key] = str(value).strip()
            
            # Don't create location property here - let Cypher handle it
            neo4j_data.append(cleaned_row)
        
        return neo4j_data
    
    def convert_places_to_neo4j(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert places CSV data to Neo4j format"""
        neo4j_data = []
        
        for row in data:
            cleaned_row = {}
            
            for key, value in row.items():
                if value == '' or value is None:
                    continue
                
                # Convert coordinates to float
                if key in ['latitude', 'longitude']:
                    try:
                        cleaned_row[key] = float(value)
                    except (ValueError, TypeError):
                        continue
                
                # Parse category IDs and labels
                elif key == 'fsq_category_ids':
                    # Remove brackets and split by comma
                    category_ids = value.strip('[]').split(',')
                    cleaned_row['category_ids'] = [cid.strip() for cid in category_ids if cid.strip()]
                
                elif key == 'fsq_category_labels':
                    # Parse nested list format ['label1', 'label2 > sublabel']
                    try:
                        # Remove outer brackets and parse
                        labels_str = value.strip('[]')
                        if labels_str.startswith("'") or labels_str.startswith('"'):
                            # Handle quoted strings
                            import ast
                            category_labels = ast.literal_eval(f"[{labels_str}]")
                        else:
                            category_labels = [label.strip().strip("'\"") for label in labels_str.split(',')]
                        cleaned_row['category_labels'] = category_labels
                    except:
                        # Fallback to simple splitting
                        cleaned_row['category_labels'] = [value.strip()]
                
                # Keep string fields
                else:
                    cleaned_row[key] = str(value).strip()
            
            # Don't create location property here - let Cypher handle it
            neo4j_data.append(cleaned_row)
        
        return neo4j_data
    
    def batch_mutate(self, data: List[Dict[str, Any]], cypher_query: str, entity_type: str = None) -> bool:
        """Send data to Neo4j in batches"""
        if not data:
            return True
        
        total_batches = (len(data) + self.batch_size - 1) // self.batch_size
        logger.info(f"Processing {total_batches} batches for {entity_type or 'data'}")
        
        with self.driver.session(database=self.config.database) as session:
            for i in range(0, len(data), self.batch_size):
                batch = data[i:i + self.batch_size]
                current_batch = (i // self.batch_size) + 1
                
                try:
                    session.execute_write(lambda tx: tx.run(cypher_query, {"batch": batch}))
                    logger.info(f"Successfully imported batch {current_batch}/{total_batches}")
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error importing batch {current_batch}/{total_batches}: {e}")
                    return False
        
        return True
    
    def import_transit_stops(self) -> bool:
        """Import transit stops data"""
        logger.info("Importing transit stops...")
        
        data = self.read_csv_file("stops.txt")
        if not data:
            logger.error("No transit stops data found")
            return False
        
        neo4j_data = self.convert_transit_stops_to_neo4j(data)
        
        cypher_query = """
        UNWIND $batch AS row
        CREATE (ts:TransitStop)
        SET ts = row,
            ts.location = point({x: row.stop_lon, y: row.stop_lat, srid: 4326})
        """
        
        success = self.batch_mutate(neo4j_data, cypher_query, "transit_stops")
        
        if success:
            self.imported_count['transit_stops'] = len(data)
            logger.info(f"Successfully imported {len(data)} transit stops")
            return True
        else:
            logger.error("Failed to import transit stops")
            return False
    
    def import_places(self) -> bool:
        """Import places data"""
        logger.info("Importing places...")
        
        data = self.read_csv_file("king_county_places_near_stops.csv")
        if not data:
            logger.error("No places data found")
            return False
        
        neo4j_data = self.convert_places_to_neo4j(data)
        
        cypher_query = """
        UNWIND $batch AS row
        CREATE (p:Place)
        SET p = row,
            p.location = point({x: row.longitude, y: row.latitude, srid: 4326})
        """
        
        success = self.batch_mutate(neo4j_data, cypher_query, "places")
        
        if success:
            self.imported_count['places'] = len(data)
            logger.info(f"Successfully imported {len(data)} places")
            return True
        else:
            logger.error("Failed to import places")
            return False
    
    def create_categories(self) -> bool:
        """Extract and create category nodes from places data"""
        logger.info("Creating categories from places data...")
        
        with self.driver.session(database=self.config.database) as session:
            try:
                # Extract unique categories
                result = session.run("""
                    MATCH (p:Place)
                    WHERE p.category_ids IS NOT NULL AND p.category_labels IS NOT NULL
                    UNWIND range(0, size(p.category_ids)-1) AS idx
                    WITH p.category_ids[idx] AS category_id, p.category_labels[idx] AS category_label
                    WHERE category_id IS NOT NULL AND category_label IS NOT NULL
                    RETURN DISTINCT category_id, category_label
                """)
                
                categories = []
                for record in result:
                    categories.append({
                        'category_id': record['category_id'],
                        'label': record['category_label']
                    })
                
                if categories:
                    # Create category nodes
                    cypher_query = """
                    UNWIND $batch AS row
                    MERGE (c:Category {category_id: row.category_id})
                    SET c.label = row.label
                    """
                    
                    success = self.batch_mutate(categories, cypher_query, "categories")
                    
                    if success:
                        self.imported_count['categories'] = len(categories)
                        logger.info(f"Successfully created {len(categories)} categories")
                        return True
                
            except Exception as e:
                logger.error(f"Error creating categories: {e}")
                return False
        
        return True
    
    def create_relationships(self) -> bool:
        """Create relationships between entities"""
        logger.info("Creating relationships...")
        
        relationships_created = 0
        
        with self.driver.session(database=self.config.database) as session:
            try:
                # Create Place -> Category relationships
                result = session.run("""
                    MATCH (p:Place), (c:Category)
                    WHERE p.category_ids IS NOT NULL AND c.category_id IN p.category_ids
                    CREATE (p)-[:BELONGS_TO_CATEGORY]->(c)
                    RETURN count(*) as relationships_created
                """)
                
                count = result.single()['relationships_created']
                relationships_created += count
                logger.info(f"Created {count} Place -> Category relationships")
                
                # Create Place -> TransitStop relationships (NEAR_STOP)
                result = session.run("""
                    MATCH (p:Place), (ts:TransitStop)
                    WHERE p.closest_stop_name IS NOT NULL 
                    AND (ts.stop_name = p.closest_stop_name OR ts.tts_stop_name = p.closest_stop_name)
                    CREATE (p)-[:NEAR_STOP]->(ts)
                    RETURN count(*) as relationships_created
                """)
                
                count = result.single()['relationships_created']
                relationships_created += count
                logger.info(f"Created {count} Place -> TransitStop relationships")
                
                # Create spatial proximity relationships (within 500m)
                result = session.run("""
                    MATCH (p:Place), (ts:TransitStop)
                    WHERE p.location IS NOT NULL AND ts.location IS NOT NULL
                    AND point.distance(p.location, ts.location) <= 500
                    MERGE (p)-[:WITHIN_500M]->(ts)
                    RETURN count(*) as relationships_created
                """)
                
                count = result.single()['relationships_created']
                relationships_created += count
                logger.info(f"Created {count} spatial proximity relationships (500m)")
                
                self.imported_count['relationships'] = relationships_created
                logger.info(f"Successfully created {relationships_created} total relationships")
                return True
                
            except Exception as e:
                logger.error(f"Error creating relationships: {e}")
                return False
    
    def import_all(self) -> bool:
        """Import all Foursquare data"""
        logger.info("Starting Foursquare import...")
        
        # Test connection
        if not self.test_connection():
            return False
        
        # Create schema
        if not self.create_schema():
            return False
        
        # Import data
        if not self.import_transit_stops():
            return False
        
        if not self.import_places():
            return False
        
        # Create categories and relationships
        if not self.create_categories():
            return False
        
        if not self.create_relationships():
            return False
        
        # Print summary
        self.print_summary()
        
        logger.info("Foursquare import completed successfully!")
        return True
    
    def print_summary(self):
        """Print import summary"""
        logger.info("=" * 50)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 50)
        
        total_imported = sum(self.imported_count.values())
        
        for entity, count in self.imported_count.items():
            logger.info(f"{entity.replace('_', ' ').title()}: {count:,}")
        
        logger.info("-" * 50)
        logger.info(f"Total entities imported: {total_imported:,}")
        logger.info("=" * 50)
    
    def close(self):
        """Close Neo4j driver"""
        if self.driver:
            self.driver.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Import Foursquare data into Neo4j")
    parser.add_argument(
        "--config-file",
        default="config.env",
        help="Configuration file path (default: config.env)"
    )
    parser.add_argument(
        "--data-dir",
        help="Directory containing Foursquare data files (overrides config)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Batch size for mutations (overrides config)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = Neo4jConfig(args.config_file)
        config.print_config()
        
        if not config.validate_connection():
            logger.error("Invalid Neo4j configuration")
            sys.exit(1)
        
        # Create importer
        importer = FoursquareImporter(
            config=config,
            data_dir=args.data_dir,
            batch_size=args.batch_size
        )
        
        try:
            # Run import
            success = importer.import_all()
            
            if success:
                logger.info("Import completed successfully!")
                sys.exit(0)
            else:
                logger.error("Import failed!")
                sys.exit(1)
        
        finally:
            importer.close()
            
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()