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
        # Simple GTFS Schema for testing
        
        # Predicates
        agency_id: string .
        agency_name: string .
        agency_url: string .
        stop_id: string .
        stop_name: string .
        stop_lat: float .
        stop_lon: float .
        
        # Types
        type Agency {
            agency_id
            agency_name
            agency_url
        }
        
        type Stop {
            stop_id
            stop_name
            stop_lat
            stop_lon
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
                if value == '':
                    continue
                
                # Convert numeric fields
                if key in ['stop_lat', 'stop_lon', 'shape_pt_lat', 'shape_pt_lon', 
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
            
            # Create Dgraph node
            dgraph_node = {
                "uid": f"_:{entity_type}_{cleaned_row.get(f'{entity_type}_id', hash(str(cleaned_row)))}",
                "dgraph.type": entity_type.capitalize(),
                **cleaned_row
            }
            
            dgraph_data.append(dgraph_node)
        
        return dgraph_data
    
    def batch_mutate(self, data: List[Dict[str, Any]]) -> bool:
        """Send data to Dgraph in batches using pydgraph"""
        if not data:
            return True
        
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            
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
                    
                    logger.info(f"Successfully imported batch {i//self.batch_size + 1}")
                    
                except Exception as e:
                    logger.error(f"Error in transaction for batch {i//self.batch_size + 1}: {e}")
                    txn.discard()
                    return False
                finally:
                    txn.discard()
                
                # Small delay to avoid overwhelming Dgraph
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error importing batch {i//self.batch_size + 1}: {e}")
                return False
        
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
                            nquads.append(f'{uid} <{key}> "{val}" .')
                        else:
                            nquads.append(f'{uid} <{key}> "{val}" .')
                elif isinstance(value, (int, float)):
                    nquads.append(f'{uid} <{key}> "{value}" .')
                else:
                    # Escape quotes in strings
                    escaped_value = str(value).replace('"', '\\"')
                    nquads.append(f'{uid} <{key}> "{escaped_value}" .')
        
        return '\n'.join(nquads)
    
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
            self.import_stops,
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
