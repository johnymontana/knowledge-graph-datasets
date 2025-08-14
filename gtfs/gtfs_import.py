#!/usr/bin/env python3
"""
GTFS to Dgraph Import Script

This script imports GTFS (General Transit Feed Specification) data into Dgraph,
creating a knowledge graph of transit information including agencies, routes,
stops, trips, and their relationships.

Requirements:
- Python 3.7+
- requests library
- pandas library

Usage:
    python gtfs_import.py [--dgraph-url DGRAPH_URL] [--data-dir DATA_DIR]
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
import requests
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
        self.dgraph_url = config.get_http_url()
        self.data_dir = Path(data_dir or os.getenv('DATA_DIR', 'data'))
        self.session = requests.Session()
        
        # Configure session with SSL and authentication
        if config.use_ssl:
            ssl_config = config.get_ssl_config()
            if ssl_config:
                self.session.verify = ssl_config.get('verify', True)
        
        # Set default headers
        self.session.headers.update(config.get_headers())
        
        # Dgraph endpoints
        self.mutate_url = f"{self.dgraph_url}/mutate"
        self.query_url = f"{self.dgraph_url}/query"
        self.alter_url = f"{self.dgraph_url}/alter"
        
        # Batch size for mutations
        self.batch_size = batch_size or int(os.getenv('BATCH_SIZE', '1000'))
        
        # Track imported entities
        self.imported_count = {
            'agencies': 0,
            'routes': 0,
            'stops': 0,
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
    
    def test_connection(self) -> bool:
        """Test connection to Dgraph"""
        try:
            response = self.session.get(f"{self.dgraph_url}/health")
            if response.status_code == 200:
                logger.info("Successfully connected to Dgraph")
                return True
            else:
                logger.error(f"Failed to connect to Dgraph: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error connecting to Dgraph: {e}")
            return False
    
    def create_schema(self) -> bool:
        """Create the Dgraph schema for GTFS data"""
        schema = """
        # GTFS Schema
        
        # Agency
        type Agency {
            agency_id: string @id
            agency_name: string
            agency_url: string
            agency_timezone: string
            agency_lang: string
            agency_phone: string
            agency_fare_url: string
            agency_email: string
            routes: [Route] @hasInverse(field: agency)
        }
        
        # Route
        type Route {
            route_id: string @id
            agency_id: string
            route_short_name: string
            route_long_name: string
            route_type: int
            route_desc: string
            route_url: string
            route_color: string
            route_text_color: string
            network_id: string
            route_sort_order: int
            agency: Agency @hasInverse(field: routes)
            trips: [Trip] @hasInverse(field: route)
        }
        
        # Stop
        type Stop {
            stop_id: string @id
            stop_name: string
            location: geo @index(geo)
            stop_code: string
            stop_desc: string
            zone_id: string
            stop_url: string
            location_type: int
            parent_station: string
            wheelchair_boarding: int
            stop_timezone: string
            platform_code: string
            tts_stop_name: string
            stop_times: [StopTime] @hasInverse(field: stop)
            transfers_from: [Transfer] @hasInverse(field: from_stop)
            transfers_to: [Transfer] @hasInverse(field: to_stop)
        }
        
        # Trip
        type Trip {
            trip_id: string @id
            route_id: string
            service_id: string
            trip_headsign: string
            trip_short_name: string
            direction_id: int
            block_id: string
            shape_id: string
            wheelchair_accessible: int
            bikes_allowed: int
            route: Route @hasInverse(field: trips)
            stop_times: [StopTime] @hasInverse(field: trip)
            calendar: Calendar @hasInverse(field: trips)
        }
        
        # StopTime
        type StopTime {
            trip_id: string
            arrival_time: string
            departure_time: string
            stop_id: string
            stop_sequence: int
            stop_headsign: string
            pickup_type: int
            drop_off_type: int
            continuous_pickup: int
            continuous_drop_off: int
            shape_dist_traveled: float
            timepoint: int
            trip: Trip @hasInverse(field: stop_times)
            stop: Stop @hasInverse(field: stop_times)
        }
        
        # Calendar
        type Calendar {
            service_id: string @id
            monday: int
            tuesday: int
            wednesday: int
            thursday: int
            friday: int
            saturday: int
            sunday: int
            start_date: string
            end_date: string
            trips: [Trip] @hasInverse(field: calendar)
            calendar_dates: [CalendarDate] @hasInverse(field: calendar)
        }
        
        # CalendarDate
        type CalendarDate {
            service_id: string
            date: string
            exception_type: int
            calendar: Calendar @hasInverse(field: calendar_dates)
        }
        
        # FareAttribute
        type FareAttribute {
            fare_id: string @id
            price: float
            currency_type: string
            payment_method: int
            transfers: int
            agency_id: string
            transfer_duration: int
            fare_rules: [FareRule] @hasInverse(field: fare_attribute)
        }
        
        # FareRule
        type FareRule {
            fare_id: string
            route_id: string
            origin_id: string
            destination_id: string
            contains_id: string
            fare_attribute: FareAttribute @hasInverse(field: fare_rules)
        }
        
        # Transfer
        type Transfer {
            from_stop_id: string
            to_stop_id: string
            transfer_type: int
            min_transfer_time: int
            from_stop: Stop @hasInverse(field: transfers_from)
            to_stop: Stop @hasInverse(field: transfers_to)
        }
        
        # Shape
        type Shape {
            shape_id: string @id
            shape_pt_lat: float
            shape_pt_lon: float
            shape_pt_sequence: int
            shape_dist_traveled: float
        }
        
        # FeedInfo
        type FeedInfo {
            feed_id: string @id
            feed_publisher_name: string
            feed_publisher_url: string
            feed_lang: string
            feed_start_date: string
            feed_end_date: string
            feed_version: string
            default_lang: string
            feed_contact_email: string
            feed_contact_url: string
        }
        """
        
        try:
            response = self.session.post(
                self.alter_url,
                data=schema,
                headers={'Content-Type': 'application/dql'}
            )
            
            if response.status_code == 200:
                logger.info("Successfully created Dgraph schema")
                return True
            else:
                logger.error(f"Failed to create schema: {response.status_code} - {response.text}")
                return False
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
                if value == '':
                    continue
                
                # Convert numeric fields
                if key in ['shape_pt_lat', 'shape_pt_lon', 
                          'shape_dist_traveled', 'price', 'min_transfer_time']:
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
                           'transfers', 'transfer_duration', 'transfer_type']:
                    try:
                        cleaned_row[key] = int(value)
                    except (ValueError, TypeError):
                        continue
                
                # Keep string fields as-is
                else:
                    cleaned_row[key] = value
            
            # Special handling for stops to create geo point
            if entity_type == "stop" and 'stop_lat' in cleaned_row and 'stop_lon' in cleaned_row:
                try:
                    lat = float(cleaned_row['stop_lat'])
                    lon = float(cleaned_row['stop_lon'])
                    # Create geo point in Dgraph format: [longitude, latitude]
                    cleaned_row['location'] = [lon, lat]
                    # Remove the old lat/lon fields
                    del cleaned_row['stop_lat']
                    del cleaned_row['stop_lon']
                except (ValueError, TypeError):
                    pass
            
            # Create Dgraph node
            dgraph_node = {
                "uid": f"_:{entity_type}_{cleaned_row.get(f'{entity_type}_id', hash(str(cleaned_row)))}",
                "dgraph.type": entity_type.capitalize(),
                **cleaned_row
            }
            
            dgraph_data.append(dgraph_node)
        
        return dgraph_data
    
    def batch_mutate(self, data: List[Dict[str, Any]]) -> bool:
        """Send data to Dgraph in batches"""
        if not data:
            return True
        
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            
            try:
                response = self.session.post(
                    self.mutate_url,
                    json={"set": batch},
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully imported batch {i//self.batch_size + 1}")
                else:
                    logger.error(f"Failed to import batch {i//self.batch_size + 1}: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return False
                
                # Small delay to avoid overwhelming Dgraph
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error importing batch {i//self.batch_size + 1}: {e}")
                return False
        
        return True
    
    def import_agencies(self) -> bool:
        """Import agency data"""
        logger.info("Importing agencies...")
        data = self.read_csv_file("agency.txt")
        if not data:
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "agency")
        success = self.batch_mutate(dgraph_data)
        
        if success:
            self.imported_count['agencies'] = len(data)
            logger.info(f"Successfully imported {len(data)} agencies")
        
        return success
    
    def import_routes(self) -> bool:
        """Import route data"""
        logger.info("Importing routes...")
        data = self.read_csv_file("routes.txt")
        if not data:
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "route")
        success = self.batch_mutate(dgraph_data)
        
        if success:
            self.imported_count['routes'] = len(data)
            logger.info(f"Successfully imported {len(data)} routes")
        
        return success
    
    def import_stops(self) -> bool:
        """Import stop data"""
        logger.info("Importing stops...")
        data = self.read_csv_file("stops.txt")
        if not data:
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "stop")
        success = self.batch_mutate(dgraph_data)
        
        if success:
            self.imported_count['stops'] = len(data)
            logger.info(f"Successfully imported {len(data)} stops")
        
        return success
    
    def import_calendar(self) -> bool:
        """Import calendar data"""
        logger.info("Importing calendar...")
        data = self.read_csv_file("calendar.txt")
        if not data:
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "service")
        success = self.batch_mutate(dgraph_data)
        
        if success:
            self.imported_count['calendar'] = len(data)
            logger.info(f"Successfully imported {len(data)} calendar entries")
        
        return success
    
    def import_calendar_dates(self) -> bool:
        """Import calendar dates data"""
        logger.info("Importing calendar dates...")
        data = self.read_csv_file("calendar_dates.txt")
        if not data:
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "service")
        success = self.batch_mutate(dgraph_data)
        
        if success:
            self.imported_count['calendar_dates'] = len(data)
            logger.info(f"Successfully imported {len(data)} calendar dates")
        
        return success
    
    def import_trips(self) -> bool:
        """Import trip data"""
        logger.info("Importing trips...")
        data = self.read_csv_file("trips.txt")
        if not data:
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "trip")
        success = self.batch_mutate(dgraph_data)
        
        if success:
            self.imported_count['trips'] = len(data)
            logger.info(f"Successfully imported {len(data)} trips")
        
        return success
    
    def import_stop_times(self) -> bool:
        """Import stop times data"""
        logger.info("Importing stop times...")
        data = self.read_csv_file("stop_times.txt")
        if not data:
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "trip")
        success = self.batch_mutate(dgraph_data)
        
        if success:
            self.imported_count['stop_times'] = len(data)
            logger.info(f"Successfully imported {len(data)} stop times")
        
        return success
    
    def import_fare_attributes(self) -> bool:
        """Import fare attributes data"""
        logger.info("Importing fare attributes...")
        data = self.read_csv_file("fare_attributes.txt")
        if not data:
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "fare")
        success = self.batch_mutate(dgraph_data)
        
        if success:
            self.imported_count['fare_attributes'] = len(data)
            logger.info(f"Successfully imported {len(data)} fare attributes")
        
        return success
    
    def import_fare_rules(self) -> bool:
        """Import fare rules data"""
        logger.info("Importing fare rules...")
        data = self.read_csv_file("fare_rules.txt")
        if not data:
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "fare")
        success = self.batch_mutate(dgraph_data)
        
        if success:
            self.imported_count['fare_rules'] = len(data)
            logger.info(f"Successfully imported {len(data)} fare rules")
        
        return success
    
    def import_transfers(self) -> bool:
        """Import transfers data"""
        logger.info("Importing transfers...")
        data = self.read_csv_file("transfers.txt")
        if not data:
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "from_stop")
        success = self.batch_mutate(dgraph_data)
        
        if success:
            self.imported_count['transfers'] = len(data)
            logger.info(f"Successfully imported {len(data)} transfers")
        
        return success
    
    def import_shapes(self) -> bool:
        """Import shapes data"""
        logger.info("Importing shapes...")
        data = self.read_csv_file("shapes.txt")
        if not data:
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "shape")
        success = self.batch_mutate(dgraph_data)
        
        if success:
            self.imported_count['shapes'] = len(data)
            logger.info(f"Successfully imported {len(data)} shape points")
        
        return success
    
    def import_feed_info(self) -> bool:
        """Import feed info data"""
        logger.info("Importing feed info...")
        data = self.read_csv_file("feed_info.txt")
        if not data:
            return False
        
        dgraph_data = self.convert_to_dgraph_format(data, "feed")
        success = self.batch_mutate(dgraph_data)
        
        if success:
            self.imported_count['feed_info'] = len(data)
            logger.info(f"Successfully imported {len(data)} feed info entries")
        
        return success
    
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
