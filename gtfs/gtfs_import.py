#!/usr/bin/env python3
"""
GTFS to Dgraph Import Script

This script imports GTFS (General Transit Feed Specification) data into Dgraph,
creating a knowledge graph of transit information including agencies, routes,
stops, trips, and their relationships.

Requirements:
- Python 3.7+
- pydgraph library
- pandas library

Usage:
    python gtfs_import.py [--config-file CONFIG_FILE] [--data-dir DATA_DIR]
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
import pydgraph
import pandas as pd
from dgraph_config import DgraphConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GTFSImporter:
    """Imports GTFS data into Dgraph"""
    
    def __init__(self, config: DgraphConfig = None, data_dir: str = None, batch_size: int = None):
        # Load configuration
        if config is None:
            config = DgraphConfig()
        
        self.config = config
        self.data_dir = Path(data_dir or os.getenv('DATA_DIR', 'data'))
        
        # Create pydgraph client using connection string
        self.client = self._create_pydgraph_client()
        
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
    
    def _create_pydgraph_client(self):
        """Create and configure pydgraph client using connection string"""
        try:
            # Use pydgraph.open() with the connection string from config
            client = pydgraph.open(self.config.connection_string)
            logger.info("Successfully created pydgraph client")
            return client
        except Exception as e:
            logger.error(f"Failed to create pydgraph client: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test connection to Dgraph using pydgraph"""
        try:
            # Test connection by running a simple query
            txn = self.client.txn()
            try:
                # Use a simple DQL query to test connection
                response = txn.query("query { }")
                logger.info("Successfully connected to Dgraph via pydgraph")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to Dgraph: {e}")
                return False
            finally:
                txn.discard()
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return False
    
    def create_schema(self) -> bool:
        """Create the Dgraph schema for GTFS data"""
        # Use simple schema for testing
        schema = """
        # Comprehensive GTFS Schema
        
        # Predicates
        agency_id: string .
        agency_name: string .
        agency_url: string .
        agency_timezone: string .
        agency_lang: string .
        agency_phone: string .
        agency_fare_url: string .
        agency_email: string .
        
        route_id: string .
        route_short_name: string .
        route_long_name: string .
        route_type: int .
        route_desc: string .
        route_url: string .
        route_color: string .
        route_text_color: string .
        network_id: string .
        route_sort_order: int .
        
        stop_id: string .
        stop_name: string .
        stop_lat: float .
        stop_lon: float .
        stop_code: string .
        stop_desc: string .
        zone_id: string .
        stop_url: string .
        location_type: int .
        parent_station: string .
        wheelchair_boarding: int .
        stop_timezone: string .
        platform_code: string .
        tts_stop_name: string .
        
        trip_id: string .
        service_id: string .
        trip_headsign: string .
        trip_short_name: string .
        direction_id: int .
        block_id: string .
        shape_id: string .
        wheelchair_accessible: int .
        bikes_allowed: int .
        
        arrival_time: string .
        departure_time: string .
        stop_sequence: int .
        stop_headsign: string .
        pickup_type: int .
        drop_off_type: int .
        continuous_pickup: int .
        continuous_drop_off: int .
        shape_dist_traveled: float .
        timepoint: int .
        
        monday: int .
        tuesday: int .
        wednesday: int .
        thursday: int .
        friday: int .
        saturday: int .
        sunday: int .
        start_date: string .
        end_date: string .
        
        date: string .
        exception_type: int .
        
        fare_id: string .
        price: float .
        currency_type: string .
        payment_method: int .
        transfers: int .
        transfer_duration: int .
        origin_id: string .
        destination_id: string .
        contains_id: string .
        
        from_stop_id: string .
        to_stop_id: string .
        from_route_id: string .
        to_route_id: string .
        transfer_type: int .
        min_transfer_time: int .
        
        shape_pt_lat: float .
        shape_pt_lon: float .
        shape_pt_sequence: int .
        
        feed_id: string .
        feed_publisher_name: string .
        feed_publisher_url: string .
        feed_lang: string .
        feed_start_date: string .
        feed_end_date: string .
        feed_version: string .
        default_lang: string .
        feed_contact_email: string .
        feed_contact_url: string .
        
        # Types
        type Agency {
            agency_id
            agency_name
            agency_url
            agency_timezone
            agency_lang
            agency_phone
            agency_fare_url
            agency_email
        }
        
        type Route {
            route_id
            agency_id
            route_short_name
            route_long_name
            route_type
            route_desc
            route_url
            route_color
            route_text_color
            network_id
            route_sort_order
        }
        
        type Stop {
            stop_id
            stop_name
            stop_lat
            stop_lon
            stop_code
            stop_desc
            zone_id
            stop_url
            location_type
            parent_station
            wheelchair_boarding
            stop_timezone
            platform_code
            tts_stop_name
        }
        
        type Trip {
            trip_id
            route_id
            service_id
            trip_headsign
            trip_short_name
            direction_id
            block_id
            shape_id
            wheelchair_accessible
            bikes_allowed
        }
        
        type StopTime {
            trip_id
            arrival_time
            departure_time
            stop_id
            stop_sequence
            stop_headsign
            pickup_type
            drop_off_type
            continuous_pickup
            continuous_drop_off
            shape_dist_traveled
            timepoint
        }
        
        type Calendar {
            service_id
            monday
            tuesday
            wednesday
            thursday
            friday
            saturday
            sunday
            start_date
            end_date
        }
        
        type CalendarDate {
            service_id
            date
            exception_type
        }
        
        type FareAttribute {
            fare_id
            price
            currency_type
            payment_method
            transfers
            agency_id
            transfer_duration
        }
        
        type FareRule {
            fare_id
            route_id
            origin_id
            destination_id
            contains_id
        }
        
        type Transfer {
            from_stop_id
            to_stop_id
            from_route_id
            to_route_id
            transfer_type
            min_transfer_time
        }
        
        type Shape {
            shape_id
            shape_pt_lat
            shape_pt_lon
            shape_pt_sequence
            shape_dist_traveled
        }
        
        type FeedInfo {
            feed_id
            feed_publisher_name
            feed_publisher_url
            feed_lang
            feed_start_date
            feed_end_date
            feed_version
            default_lang
            feed_contact_email
            feed_contact_url
        }
        """
        
        try:
            # Use pydgraph to alter the schema
            op = pydgraph.Operation(schema=schema)
            response = self.client.alter(op)
            logger.info("Successfully created Dgraph schema")
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
    
    def convert_to_dgraph_format(self, data: List[Dict[str, Any]], entity_type: str) -> List[Dict[str, Any]]:
        """Convert CSV data to Dgraph mutation format"""
        dgraph_data = []
        
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
                
                # Convert integer fields (including min_transfer_time)
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
                    cleaned_row[key] = value
            
            # Create Dgraph node
            # Generate a clean UID that's safe for N-Quads
            entity_id = cleaned_row.get(f'{entity_type}_id', str(hash(str(cleaned_row))))
            # Clean the entity_id to make it safe for N-Quads
            clean_entity_id = entity_id.replace(' ', '_').replace(':', '_').replace('-', '_').replace('"', '').replace("'", '')
            dgraph_node = {
                "uid": f"_:{entity_type}_{clean_entity_id}",
                "dgraph.type": entity_type.capitalize(),
                **cleaned_row
            }
            
            dgraph_data.append(dgraph_node)
        
        return dgraph_data
    
    def batch_mutate(self, data: List[Dict[str, Any]], entity_type: str = None, resume_from_batch: int = 0) -> bool:
        """Send data to Dgraph in batches using pydgraph with resume support"""
        if not data:
            return True
        
        total_batches = (len(data) + self.batch_size - 1) // self.batch_size
        start_batch = resume_from_batch
        
        logger.info(f"Processing {total_batches} batches for {entity_type or 'data'} (resuming from batch {start_batch + 1})")
        
        for i in range(start_batch * self.batch_size, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            current_batch = i // self.batch_size + 1
            
            try:
                # Create transaction
                txn = self.client.txn()
                try:
                    # Convert to N-Quads format for pydgraph
                    nquads = self._convert_to_nquads(batch)
                    
                    # Perform mutation
                    response = txn.mutate(set_nquads=nquads)
                    
                    # Commit transaction
                    txn.commit()
                    
                    logger.info(f"Successfully imported batch {current_batch}/{total_batches}")
                    
                    # Update progress if entity_type is provided
                    if entity_type:
                        self._update_progress(entity_type, current_batch, total_batches)
                    
                except Exception as e:
                    logger.error(f"Error in transaction for batch {current_batch}/{total_batches}: {e}")
                    txn.discard()
                    return False
                finally:
                    txn.discard()
                
                # Small delay to avoid overwhelming Dgraph
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error importing batch {current_batch}/{total_batches}: {e}")
                return False
        
        # Mark as completed if entity_type is provided
        if entity_type:
            self._update_progress(entity_type, total_batches, total_batches, completed=True)
        
        return True
    
    def _convert_to_nquads(self, data: List[Dict[str, Any]]) -> str:
        """Convert Dgraph data to N-Quads format"""
        nquads = []
        
        for item in data:
            uid = item.get('uid', '_:new')
            dgraph_type = item.get('dgraph.type', 'Entity')
            
            # Add type
            nquads.append(f'{uid} <dgraph.type> "{dgraph_type}" .')
            
            # Add properties
            for key, value in item.items():
                if key in ['uid', 'dgraph.type']:
                    continue
                
                if isinstance(value, list):
                    # Handle list values
                    for val in value:
                        if isinstance(val, str):
                            # Clean string values
                            clean_val = str(val).replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
                            nquads.append(f'{uid} <{key}> "{clean_val}" .')
                        else:
                            nquads.append(f'{uid} <{key}> "{val}" .')
                elif isinstance(value, (int, float)):
                    nquads.append(f'{uid} <{key}> "{value}" .')
                else:
                    # Clean string values - escape quotes and remove newlines
                    clean_value = str(value).replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
                    nquads.append(f'{uid} <{key}> "{clean_value}" .')
        
        return '\n'.join(nquads)
    
    def import_agencies(self) -> bool:
        """Import agency data"""
        # Check if already completed
        if self.import_progress['agencies']['completed']:
            logger.info("Agencies already imported, skipping...")
            return True
            
        logger.info("Importing agencies...")
        data = self.read_csv_file("agency.txt")
        if not data:
            logger.error("No agency data found")
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "agency")
        
        # Get resume point
        resume_from = self._get_resume_point("agencies")
        success = self.batch_mutate(dgraph_data, "agencies", resume_from)
        
        if success:
            self.imported_count['agencies'] = len(data)
            logger.info(f"Successfully imported {len(data)} agencies")
            return True
        else:
            logger.error("Failed to import agencies")
            return False
    
    def import_stops(self) -> bool:
        """Import stop data"""
        # Check if already completed
        if self.import_progress['stops']['completed']:
            logger.info("Stops already imported, skipping...")
            return True
            
        logger.info("Importing stops...")
        data = self.read_csv_file("stops.txt")
        if not data:
            logger.error("No stops data found")
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "stop")
        
        # Get resume point
        resume_from = self._get_resume_point("stops")
        success = self.batch_mutate(dgraph_data, "stops", resume_from)
        
        if success:
            self.imported_count['stops'] = len(data)
            logger.info(f"Successfully imported {len(data)} stops")
            return True
        else:
            logger.error("Failed to import stops")
            return False
    
    def import_routes(self) -> bool:
        """Import route data"""
        # Check if already completed
        if self.import_progress['routes']['completed']:
            logger.info("Routes already imported, skipping...")
            return True
            
        logger.info("Importing routes...")
        data = self.read_csv_file("routes.txt")
        if not data:
            logger.error("No routes data found")
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "route")
        
        # Get resume point
        resume_from = self._get_resume_point("routes")
        success = self.batch_mutate(dgraph_data, "routes", resume_from)
        
        if success:
            self.imported_count['routes'] = len(data)
            logger.info(f"Successfully imported {len(data)} routes")
            return True
        else:
            logger.error("Failed to import routes")
            return False
    
    def import_calendar(self) -> bool:
        """Import calendar data"""
        # Check if already completed
        if self.import_progress['calendar']['completed']:
            logger.info("Calendar already imported, skipping...")
            return True
            
        logger.info("Importing calendar...")
        data = self.read_csv_file("calendar.txt")
        if not data:
            logger.error("No calendar data found")
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "calendar")
        
        # Get resume point
        resume_from = self._get_resume_point("calendar")
        success = self.batch_mutate(dgraph_data, "calendar", resume_from)
        
        if success:
            self.imported_count['calendar'] = len(data)
            logger.info(f"Successfully imported {len(data)} calendar entries")
            return True
        else:
            logger.error("Failed to import calendar")
            return False
    
    def import_calendar_dates(self) -> bool:
        """Import calendar dates data"""
        # Check if already completed
        if self.import_progress['calendar_dates']['completed']:
            logger.info("Calendar dates already imported, skipping...")
            return True
            
        logger.info("Importing calendar dates...")
        data = self.read_csv_file("calendar_dates.txt")
        if not data:
            logger.error("No calendar dates data found")
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "calendar_date")
        
        # Get resume point
        resume_from = self._get_resume_point("calendar_dates")
        success = self.batch_mutate(dgraph_data, "calendar_dates", resume_from)
        
        if success:
            self.imported_count['calendar_dates'] = len(data)
            logger.info(f"Successfully imported {len(data)} calendar dates")
            return True
        else:
            logger.error("Failed to import calendar dates")
            return False
    
    def import_trips(self) -> bool:
        """Import trip data"""
        # Check if already completed
        if self.import_progress['trips']['completed']:
            logger.info("Trips already imported, skipping...")
            return True
            
        logger.info("Importing trips...")
        data = self.read_csv_file("trips.txt")
        if not data:
            logger.error("No trips data found")
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "trip")
        
        # Get resume point
        resume_from = self._get_resume_point("trips")
        success = self.batch_mutate(dgraph_data, "trips", resume_from)
        
        if success:
            self.imported_count['trips'] = len(data)
            logger.info(f"Successfully imported {len(data)} trips")
            return True
        else:
            logger.error("Failed to import trips")
            return False
    
    def import_stop_times(self) -> bool:
        """Import stop times data"""
        # Check if already completed
        if self.import_progress['stop_times']['completed']:
            logger.info("Stop times already imported, skipping...")
            return True
            
        logger.info("Importing stop times...")
        data = self.read_csv_file("stop_times.txt")
        if not data:
            logger.error("No stop times data found")
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "stop_time")
        
        # Get resume point
        resume_from = self._get_resume_point("stop_times")
        success = self.batch_mutate(dgraph_data, "stop_times", resume_from)
        
        if success:
            self.imported_count['stop_times'] = len(data)
            logger.info(f"Successfully imported {len(data)} stop times")
            return True
        else:
            logger.error("Failed to import stop times")
            return False
    
    def import_fare_attributes(self) -> bool:
        """Import fare attributes data"""
        # Check if already completed
        if self.import_progress['fare_attributes']['completed']:
            logger.info("Fare attributes already imported, skipping...")
            return True
            
        logger.info("Importing fare attributes...")
        data = self.read_csv_file("fare_attributes.txt")
        if not data:
            logger.error("No fare attributes data found")
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "fare_attribute")
        
        # Get resume point
        resume_from = self._get_resume_point("fare_attributes")
        success = self.batch_mutate(dgraph_data, "fare_attributes", resume_from)
        
        if success:
            self.imported_count['fare_attributes'] = len(data)
            logger.info(f"Successfully imported {len(data)} fare attributes")
            return True
        else:
            logger.error("Failed to import fare attributes")
            return False
    
    def import_fare_rules(self) -> bool:
        """Import fare rules data"""
        # Check if already completed
        if self.import_progress['fare_rules']['completed']:
            logger.info("Fare rules already imported, skipping...")
            return True
            
        logger.info("Importing fare rules...")
        data = self.read_csv_file("fare_rules.txt")
        if not data:
            logger.error("No fare rules data found")
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "fare_rule")
        
        # Get resume point
        resume_from = self._get_resume_point("fare_rules")
        success = self.batch_mutate(dgraph_data, "fare_rules", resume_from)
        
        if success:
            self.imported_count['fare_rules'] = len(data)
            logger.info(f"Successfully imported {len(data)} fare rules")
            return True
        else:
            logger.error("Failed to import fare rules")
            return False
    
    def import_transfers(self) -> bool:
        """Import transfers data"""
        # Check if already completed
        if self.import_progress['transfers']['completed']:
            logger.info("Transfers already imported, skipping...")
            return True
            
        logger.info("Importing transfers...")
        data = self.read_csv_file("transfers.txt")
        if not data:
            logger.error("No transfers data found")
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "transfer")
        
        # Get resume point
        resume_from = self._get_resume_point("transfers")
        success = self.batch_mutate(dgraph_data, "transfers", resume_from)
        
        if success:
            self.imported_count['transfers'] = len(data)
            logger.info(f"Successfully imported {len(data)} transfers")
            return True
        else:
            logger.error("Failed to import transfers")
            return False
    
    def import_shapes(self) -> bool:
        """Import shapes data"""
        # Check if already completed
        if self.import_progress['shapes']['completed']:
            logger.info("Shapes already imported, skipping...")
            return True
            
        logger.info("Importing shapes...")
        data = self.read_csv_file("shapes.txt")
        if not data:
            logger.error("No shapes data found")
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "shape")
        
        # Get resume point
        resume_from = self._get_resume_point("shapes")
        success = self.batch_mutate(dgraph_data, "shapes", resume_from)
        
        if success:
            self.imported_count['shapes'] = len(data)
            logger.info(f"Successfully imported {len(data)} shapes")
            return True
        else:
            logger.error("Failed to import shapes")
            return False
    
    def import_feed_info(self) -> bool:
        """Import feed info data"""
        # Check if already completed
        if self.import_progress['feed_info']['completed']:
            logger.info("Feed info already imported, skipping...")
            return True
            
        logger.info("Importing feed info...")
        data = self.read_csv_file("feed_info.txt")
        if not data:
            logger.error("No feed info data found")
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "feed_info")
        
        # Get resume point
        resume_from = self._get_resume_point("feed_info")
        success = self.batch_mutate(dgraph_data, "feed_info", resume_from)
        
        if success:
            self.imported_count['feed_info'] = len(data)
            logger.info(f"Successfully imported {len(data)} feed info entries")
            return True
        else:
            logger.error("Failed to import feed info")
            return False
    
    def import_all(self) -> bool:
        """Import all GTFS data"""
        logger.info("Starting GTFS import...")
        
        # Test connection - temporarily disabled
        # if not self.test_connection():
        #     return False
        
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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Import GTFS data into Dgraph")
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
        config = DgraphConfig(args.config_file)
        config.print_config()
        
        if not config.validate_connection():
            logger.error("Invalid Dgraph configuration")
            sys.exit(1)
        
        # Create importer
        importer = GTFSImporter(
            config=config,
            data_dir=args.data_dir,
            batch_size=args.batch_size
        )
        
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
            
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
