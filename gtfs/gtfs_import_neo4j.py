#!/usr/bin/env python3
"""
GTFS to Neo4j Import Script

This script imports GTFS (General Transit Feed Specification) data into Neo4j,
creating a knowledge graph of transit information including agencies, routes,
stops, trips, and their relationships.

Requirements:
- Python 3.7+
- neo4j library
- pandas library

Usage:
    python gtfs_import_neo4j.py [--config-file CONFIG_FILE] [--data-dir DATA_DIR]
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
from neo4j_config import Neo4jConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GTFSImporter:
    """Imports GTFS data into Neo4j"""
    
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
            'agencies': 0,
            'stops': 0,
            'routes': 0,
            'trips': 0,
            'stop_times': 0,
            'calendar': 0,
            'calendar_dates': 0,
            'fare_attributes': 0,
            'fare_rules': 0,
            'transfers': 0,
            'shapes': 0,
            'feed_info': 0
        }
        
        # Progress tracking for resuming failed imports
        self.import_progress = {
            'agencies': {'completed': False, 'batches_processed': 0, 'total_batches': 0},
            'stops': {'completed': False, 'batches_processed': 0, 'total_batches': 0},
            'routes': {'completed': False, 'batches_processed': 0, 'total_batches': 0},
            'trips': {'completed': False, 'batches_processed': 0, 'total_batches': 0},
            'stop_times': {'completed': False, 'batches_processed': 0, 'total_batches': 0},
            'calendar': {'completed': False, 'batches_processed': 0, 'total_batches': 0},
            'calendar_dates': {'completed': False, 'batches_processed': 0, 'total_batches': 0},
            'fare_attributes': {'completed': False, 'batches_processed': 0, 'total_batches': 0},
            'fare_rules': {'completed': False, 'batches_processed': 0, 'total_batches': 0},
            'transfers': {'completed': False, 'batches_processed': 0, 'total_batches': 0},
            'shapes': {'completed': False, 'batches_processed': 0, 'total_batches': 0},
            'feed_info': {'completed': False, 'batches_processed': 0, 'total_batches': 0}
        }
        
        # Load progress from file if it exists
        self._load_progress()
    
    def _load_progress(self):
        """Load import progress from file"""
        progress_file = self.data_dir / '.import_progress.json'
        if progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    saved_progress = json.load(f)
                    # Update progress with saved data
                    for entity_type, progress in saved_progress.items():
                        if entity_type in self.import_progress:
                            self.import_progress[entity_type].update(progress)
                logger.info("Loaded import progress from previous session")
            except Exception as e:
                logger.warning(f"Could not load progress file: {e}")
    
    def _save_progress(self):
        """Save current import progress to file"""
        progress_file = self.data_dir / '.import_progress.json'
        try:
            with open(progress_file, 'w') as f:
                json.dump(self.import_progress, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save progress file: {e}")
    
    def _update_progress(self, entity_type: str, batches_processed: int, total_batches: int, completed: bool = False):
        """Update progress for a specific entity type"""
        if entity_type in self.import_progress:
            self.import_progress[entity_type]['batches_processed'] = batches_processed
            self.import_progress[entity_type]['total_batches'] = total_batches
            self.import_progress[entity_type]['completed'] = completed
            self._save_progress()
    
    def _get_resume_point(self, entity_type: str) -> int:
        """Get the batch number to resume from for a specific entity type"""
        if entity_type in self.import_progress:
            return self.import_progress[entity_type]['batches_processed']
        return 0
    
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
        """Create the Neo4j schema for GTFS data"""
        schema_file = Path(__file__).parent / "neo4j_schema.cypher"
        
        try:
            with self.driver.session(database=self.config.database) as session:
                # Read and execute schema file
                if schema_file.exists():
                    with open(schema_file, 'r') as f:
                        schema_content = f.read()
                    
                    # Split by lines and execute each constraint/index separately
                    for line in schema_content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('//'):
                            try:
                                session.run(line)
                            except Exception as e:
                                # Some constraints might already exist, that's OK
                                if "already exists" not in str(e).lower():
                                    logger.warning(f"Schema command failed: {line} - {e}")
                else:
                    # Create basic constraints if schema file doesn't exist
                    constraints = [
                        "CREATE CONSTRAINT agency_id_unique IF NOT EXISTS FOR (a:Agency) REQUIRE a.agency_id IS UNIQUE",
                        "CREATE CONSTRAINT route_id_unique IF NOT EXISTS FOR (r:Route) REQUIRE r.route_id IS UNIQUE", 
                        "CREATE CONSTRAINT stop_id_unique IF NOT EXISTS FOR (s:Stop) REQUIRE s.stop_id IS UNIQUE",
                        "CREATE CONSTRAINT trip_id_unique IF NOT EXISTS FOR (t:Trip) REQUIRE t.trip_id IS UNIQUE"
                    ]
                    
                    for constraint in constraints:
                        try:
                            session.run(constraint)
                        except Exception as e:
                            if "already exists" not in str(e).lower():
                                logger.warning(f"Constraint creation failed: {constraint} - {e}")
            
            logger.info("Successfully created Neo4j schema")
            return True
        except Exception as e:
            logger.error(f"Error creating schema: {e}")
            return False
    
    def read_csv_file(self, filename: str) -> List[Dict[str, Any]]:
        """Read a CSV file and return list of dictionaries"""
        filepath = self.data_dir / filename
        if not filepath.exists():
            logger.warning(f"File {filename} not found")
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            logger.error(f"Error reading {filename}: {e}")
            return []
    
    def convert_to_neo4j_format(self, data: List[Dict[str, Any]], entity_type: str) -> List[Dict[str, Any]]:
        """Convert CSV data to Neo4j format"""
        neo4j_data = []
        
        for row in data:
            # Clean and convert data types
            cleaned_row = {}
            for key, value in row.items():
                # Skip empty values
                if value == '' or value is None:
                    continue
                
                # Convert numeric fields
                if key in ['stop_lat', 'stop_lon', 'shape_pt_lat', 'shape_pt_lon', 
                          'shape_dist_traveled', 'price']:
                    try:
                        cleaned_row[key] = float(value)
                    except (ValueError, TypeError):
                        continue
                
                # Convert integer fields
                elif key in ['route_type', 'location_type', 'wheelchair_boarding', 
                           'direction_id', 'wheelchair_accessible', 'bikes_allowed',
                           'stop_sequence', 'pickup_type', 'drop_off_type', 
                           'continuous_pickup', 'continuous_drop_off', 'timepoint',
                           'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 
                           'saturday', 'sunday', 'exception_type', 'payment_method', 
                           'transfers', 'transfer_duration', 'transfer_type', 'min_transfer_time']:
                    try:
                        # Handle float values that should be integers
                        if isinstance(value, str) and '.' in value:
                            value = float(value)
                        cleaned_row[key] = int(float(value))
                    except (ValueError, TypeError):
                        continue
                
                # Keep string fields as-is
                else:
                    cleaned_row[key] = str(value).strip()
            
            neo4j_data.append(cleaned_row)
        
        return neo4j_data
    
    def batch_mutate(self, data: List[Dict[str, Any]], entity_type: str = None, resume_from_batch: int = 0) -> bool:
        """Send data to Neo4j in batches with resume support"""
        if not data:
            return True
        
        total_batches = (len(data) + self.batch_size - 1) // self.batch_size
        start_batch = resume_from_batch
        
        logger.info(f"Processing {total_batches} batches for {entity_type or 'data'} (resuming from batch {start_batch + 1})")
        
        # Generate Cypher query based on entity type
        cypher_query = self._generate_cypher_create(entity_type)
        
        with self.driver.session(database=self.config.database) as session:
            for i in range(start_batch * self.batch_size, len(data), self.batch_size):
                batch = data[i:i + self.batch_size]
                current_batch = i // self.batch_size + 1
                
                try:
                    # Execute batch as transaction
                    session.execute_write(lambda tx: tx.run(cypher_query, {"batch": batch}))
                    
                    logger.info(f"Successfully imported batch {current_batch}/{total_batches}")
                    
                    # Update progress if entity_type is provided
                    if entity_type:
                        self._update_progress(entity_type, current_batch, total_batches)
                    
                    # Small delay to avoid overwhelming Neo4j
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error importing batch {current_batch}/{total_batches}: {e}")
                    return False
        
        # Mark as completed if entity_type is provided
        if entity_type:
            self._update_progress(entity_type, total_batches, total_batches, completed=True)
        
        return True
    
    def _generate_cypher_create(self, entity_type: str) -> str:
        """Generate Cypher CREATE query for entity type"""
        label_map = {
            'agency': 'Agency',
            'stop': 'Stop', 
            'route': 'Route',
            'trip': 'Trip',
            'stop_time': 'StopTime',
            'calendar': 'Calendar',
            'calendar_date': 'CalendarDate',
            'fare_attribute': 'FareAttribute',
            'fare_rule': 'FareRule',
            'transfer': 'Transfer',
            'shape': 'Shape',
            'feed_info': 'FeedInfo'
        }
        
        label = label_map.get(entity_type, 'Entity')
        
        return f"""
        UNWIND $batch AS row
        CREATE (n:{label})
        SET n = row
        """
    
    def import_agencies(self) -> bool:
        """Import agency data"""
        if self.import_progress['agencies']['completed']:
            logger.info("Agencies already imported, skipping...")
            return True
            
        logger.info("Importing agencies...")
        data = self.read_csv_file("agency.txt")
        if not data:
            logger.error("No agency data found")
            return False
        
        neo4j_data = self.convert_to_neo4j_format(data, "agency")
        
        resume_from = self._get_resume_point("agencies")
        success = self.batch_mutate(neo4j_data, "agencies", resume_from)
        
        if success:
            self.imported_count['agencies'] = len(data)
            logger.info(f"Successfully imported {len(data)} agencies")
            return True
        else:
            logger.error("Failed to import agencies")
            return False
    
    def import_stops(self) -> bool:
        """Import stop data"""
        if self.import_progress['stops']['completed']:
            logger.info("Stops already imported, skipping...")
            return True
            
        logger.info("Importing stops...")
        data = self.read_csv_file("stops.txt")
        if not data:
            logger.error("No stops data found")
            return False
        
        neo4j_data = self.convert_to_neo4j_format(data, "stop")
        
        resume_from = self._get_resume_point("stops")
        success = self.batch_mutate(neo4j_data, "stops", resume_from)
        
        if success:
            self.imported_count['stops'] = len(data)
            logger.info(f"Successfully imported {len(data)} stops")
            return True
        else:
            logger.error("Failed to import stops")
            return False
    
    def import_routes(self) -> bool:
        """Import route data"""
        if self.import_progress['routes']['completed']:
            logger.info("Routes already imported, skipping...")
            return True
            
        logger.info("Importing routes...")
        data = self.read_csv_file("routes.txt")
        if not data:
            logger.error("No routes data found")
            return False
        
        neo4j_data = self.convert_to_neo4j_format(data, "route")
        
        resume_from = self._get_resume_point("routes")
        success = self.batch_mutate(neo4j_data, "routes", resume_from)
        
        if success:
            self.imported_count['routes'] = len(data)
            logger.info(f"Successfully imported {len(data)} routes")
            return True
        else:
            logger.error("Failed to import routes")
            return False
    
    def import_calendar(self) -> bool:
        """Import calendar data"""
        if self.import_progress['calendar']['completed']:
            logger.info("Calendar already imported, skipping...")
            return True
            
        logger.info("Importing calendar...")
        data = self.read_csv_file("calendar.txt")
        if not data:
            logger.error("No calendar data found")
            return False
        
        neo4j_data = self.convert_to_neo4j_format(data, "calendar")
        
        resume_from = self._get_resume_point("calendar")
        success = self.batch_mutate(neo4j_data, "calendar", resume_from)
        
        if success:
            self.imported_count['calendar'] = len(data)
            logger.info(f"Successfully imported {len(data)} calendar entries")
            return True
        else:
            logger.error("Failed to import calendar")
            return False
    
    def import_calendar_dates(self) -> bool:
        """Import calendar dates data"""
        if self.import_progress['calendar_dates']['completed']:
            logger.info("Calendar dates already imported, skipping...")
            return True
            
        logger.info("Importing calendar dates...")
        data = self.read_csv_file("calendar_dates.txt")
        if not data:
            logger.error("No calendar dates data found")
            return False
        
        neo4j_data = self.convert_to_neo4j_format(data, "calendar_date")
        
        resume_from = self._get_resume_point("calendar_dates")
        success = self.batch_mutate(neo4j_data, "calendar_dates", resume_from)
        
        if success:
            self.imported_count['calendar_dates'] = len(data)
            logger.info(f"Successfully imported {len(data)} calendar dates")
            return True
        else:
            logger.error("Failed to import calendar dates")
            return False
    
    def import_trips(self) -> bool:
        """Import trip data"""
        if self.import_progress['trips']['completed']:
            logger.info("Trips already imported, skipping...")
            return True
            
        logger.info("Importing trips...")
        data = self.read_csv_file("trips.txt")
        if not data:
            logger.error("No trips data found")
            return False
        
        neo4j_data = self.convert_to_neo4j_format(data, "trip")
        
        resume_from = self._get_resume_point("trips")
        success = self.batch_mutate(neo4j_data, "trips", resume_from)
        
        if success:
            self.imported_count['trips'] = len(data)
            logger.info(f"Successfully imported {len(data)} trips")
            return True
        else:
            logger.error("Failed to import trips")
            return False
    
    def import_stop_times(self) -> bool:
        """Import stop times data"""
        if self.import_progress['stop_times']['completed']:
            logger.info("Stop times already imported, skipping...")
            return True
            
        logger.info("Importing stop times...")
        data = self.read_csv_file("stop_times.txt")
        if not data:
            logger.error("No stop times data found")
            return False
        
        neo4j_data = self.convert_to_neo4j_format(data, "stop_time")
        
        resume_from = self._get_resume_point("stop_times")
        success = self.batch_mutate(neo4j_data, "stop_times", resume_from)
        
        if success:
            self.imported_count['stop_times'] = len(data)
            logger.info(f"Successfully imported {len(data)} stop times")
            return True
        else:
            logger.error("Failed to import stop times")
            return False
    
    def import_fare_attributes(self) -> bool:
        """Import fare attributes data"""
        if self.import_progress['fare_attributes']['completed']:
            logger.info("Fare attributes already imported, skipping...")
            return True
            
        logger.info("Importing fare attributes...")
        data = self.read_csv_file("fare_attributes.txt")
        if not data:
            logger.error("No fare attributes data found")
            return False
        
        neo4j_data = self.convert_to_neo4j_format(data, "fare_attribute")
        
        resume_from = self._get_resume_point("fare_attributes")
        success = self.batch_mutate(neo4j_data, "fare_attributes", resume_from)
        
        if success:
            self.imported_count['fare_attributes'] = len(data)
            logger.info(f"Successfully imported {len(data)} fare attributes")
            return True
        else:
            logger.error("Failed to import fare attributes")
            return False
    
    def import_fare_rules(self) -> bool:
        """Import fare rules data"""
        if self.import_progress['fare_rules']['completed']:
            logger.info("Fare rules already imported, skipping...")
            return True
            
        logger.info("Importing fare rules...")
        data = self.read_csv_file("fare_rules.txt")
        if not data:
            logger.error("No fare rules data found")
            return False
        
        neo4j_data = self.convert_to_neo4j_format(data, "fare_rule")
        
        resume_from = self._get_resume_point("fare_rules")
        success = self.batch_mutate(neo4j_data, "fare_rules", resume_from)
        
        if success:
            self.imported_count['fare_rules'] = len(data)
            logger.info(f"Successfully imported {len(data)} fare rules")
            return True
        else:
            logger.error("Failed to import fare rules")
            return False
    
    def import_transfers(self) -> bool:
        """Import transfers data"""
        if self.import_progress['transfers']['completed']:
            logger.info("Transfers already imported, skipping...")
            return True
            
        logger.info("Importing transfers...")
        data = self.read_csv_file("transfers.txt")
        if not data:
            logger.error("No transfers data found")
            return False
        
        neo4j_data = self.convert_to_neo4j_format(data, "transfer")
        
        resume_from = self._get_resume_point("transfers")
        success = self.batch_mutate(neo4j_data, "transfers", resume_from)
        
        if success:
            self.imported_count['transfers'] = len(data)
            logger.info(f"Successfully imported {len(data)} transfers")
            return True
        else:
            logger.error("Failed to import transfers")
            return False
    
    def import_shapes(self) -> bool:
        """Import shapes data"""
        if self.import_progress['shapes']['completed']:
            logger.info("Shapes already imported, skipping...")
            return True
            
        logger.info("Importing shapes...")
        data = self.read_csv_file("shapes.txt")
        if not data:
            logger.error("No shapes data found")
            return False
        
        neo4j_data = self.convert_to_neo4j_format(data, "shape")
        
        resume_from = self._get_resume_point("shapes")
        success = self.batch_mutate(neo4j_data, "shapes", resume_from)
        
        if success:
            self.imported_count['shapes'] = len(data)
            logger.info(f"Successfully imported {len(data)} shapes")
            return True
        else:
            logger.error("Failed to import shapes")
            return False
    
    def import_feed_info(self) -> bool:
        """Import feed info data"""
        if self.import_progress['feed_info']['completed']:
            logger.info("Feed info already imported, skipping...")
            return True
            
        logger.info("Importing feed info...")
        data = self.read_csv_file("feed_info.txt")
        if not data:
            logger.error("No feed info data found")
            return False
        
        neo4j_data = self.convert_to_neo4j_format(data, "feed_info")
        
        resume_from = self._get_resume_point("feed_info")
        success = self.batch_mutate(neo4j_data, "feed_info", resume_from)
        
        if success:
            self.imported_count['feed_info'] = len(data)
            logger.info(f"Successfully imported {len(data)} feed info entries")
            return True
        else:
            logger.error("Failed to import feed info")
            return False
    
    def create_relationships(self) -> bool:
        """Create relationships between entities"""
        logger.info("Creating relationships...")
        
        with self.driver.session(database=self.config.database) as session:
            try:
                # Create Agency -> Route relationships
                session.run("""
                    MATCH (a:Agency), (r:Route)
                    WHERE a.agency_id = r.agency_id
                    CREATE (a)-[:OPERATES]->(r)
                """)
                
                # Create Route -> Trip relationships  
                session.run("""
                    MATCH (r:Route), (t:Trip)
                    WHERE r.route_id = t.route_id
                    CREATE (r)-[:HAS_TRIP]->(t)
                """)
                
                # Create Trip -> StopTime relationships
                session.run("""
                    MATCH (t:Trip), (st:StopTime)
                    WHERE t.trip_id = st.trip_id
                    CREATE (t)-[:HAS_STOP_TIME]->(st)
                """)
                
                # Create StopTime -> Stop relationships
                session.run("""
                    MATCH (st:StopTime), (s:Stop)
                    WHERE st.stop_id = s.stop_id
                    CREATE (st)-[:AT_STOP]->(s)
                """)
                
                # Create Calendar -> Trip relationships
                session.run("""
                    MATCH (c:Calendar), (t:Trip)
                    WHERE c.service_id = t.service_id
                    CREATE (c)-[:SCHEDULES]->(t)
                """)
                
                logger.info("Successfully created relationships")
                return True
                
            except Exception as e:
                logger.error(f"Error creating relationships: {e}")
                return False
    
    def import_all(self) -> bool:
        """Import all GTFS data"""
        logger.info("Starting GTFS import...")
        
        # Test connection
        if not self.test_connection():
            return False
        
        # Create schema
        if not self.create_schema():
            return False
        
        # Import data in order (respecting dependencies)
        import_functions = [
            self.import_agencies,
            self.import_routes,
            self.import_stops,
            self.import_calendar,
            self.import_calendar_dates,
            self.import_trips,
            self.import_stop_times,
            self.import_fare_attributes,
            self.import_fare_rules,
            self.import_transfers,
            self.import_shapes,
            self.import_feed_info
        ]
        
        for import_func in import_functions:
            if not import_func():
                logger.error(f"Failed to import data with {import_func.__name__}")
                return False
        
        # Create relationships
        if not self.create_relationships():
            logger.error("Failed to create relationships")
            return False
        
        # Print summary
        self.print_summary()
        
        logger.info("GTFS import completed successfully!")
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
    
    def show_progress(self):
        """Show current import progress"""
        logger.info("=" * 50)
        logger.info("IMPORT PROGRESS")
        logger.info("=" * 50)
        
        for entity_type, progress in self.import_progress.items():
            status = "✅ COMPLETED" if progress['completed'] else "🔄 IN PROGRESS" if progress['batches_processed'] > 0 else "⏳ PENDING"
            batches_info = f"({progress['batches_processed']}/{progress['total_batches']})" if progress['total_batches'] > 0 else ""
            logger.info(f"{entity_type.replace('_', ' ').title()}: {status} {batches_info}")
        
        logger.info("=" * 50)
    
    def reset_progress(self):
        """Reset all import progress"""
        for entity_type in self.import_progress:
            self.import_progress[entity_type] = {
                'completed': False,
                'batches_processed': 0,
                'total_batches': 0
            }
        self._save_progress()
        logger.info("Import progress has been reset")
    
    def clear_progress_file(self):
        """Remove the progress file completely"""
        progress_file = self.data_dir / '.import_progress.json'
        if progress_file.exists():
            progress_file.unlink()
            logger.info("Progress file has been removed")
        else:
            logger.info("No progress file found to remove")
    
    def close(self):
        """Close Neo4j driver"""
        if self.driver:
            self.driver.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Import GTFS data into Neo4j")
    parser.add_argument(
        "--config-file",
        default="config.env",
        help="Configuration file path (default: config.env)"
    )
    parser.add_argument(
        "--data-dir",
        help="Directory containing GTFS data files (overrides config)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Batch size for mutations (overrides config)"
    )
    parser.add_argument(
        "--show-progress",
        action="store_true",
        help="Show current import progress and exit"
    )
    parser.add_argument(
        "--reset-progress",
        action="store_true",
        help="Reset all import progress and exit"
    )
    parser.add_argument(
        "--clear-progress",
        action="store_true",
        help="Remove progress file completely and exit"
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
        importer = GTFSImporter(
            config=config,
            data_dir=args.data_dir,
            batch_size=args.batch_size
        )
        
        try:
            # Handle special commands
            if args.show_progress:
                importer.show_progress()
                sys.exit(0)
            
            if args.reset_progress:
                importer.reset_progress()
                sys.exit(0)

            if args.clear_progress:
                importer.clear_progress_file()
                sys.exit(0)
            
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