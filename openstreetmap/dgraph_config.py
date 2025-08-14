#!/usr/bin/env python3
"""
Dgraph Configuration Management for OSM Import

This module handles configuration loading and Dgraph connection setup
for the OpenStreetMap data import project.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DgraphConfig:
    """Configuration class for Dgraph connection and import settings."""
    
    def __init__(self):
        self.connection_string = os.getenv('DGRAPH_CONNECTION_STRING')
        self.batch_size = int(os.getenv('BATCH_SIZE', '1000'))
        self.data_dir = os.getenv('DATA_DIR', 'data')
        
        # OSM-specific configuration
        self.osm_location = os.getenv('OSM_LOCATION', 'San Francisco, California')
        self.osm_tags = os.getenv('OSM_TAGS', 'amenity=restaurant')
        self.osm_output_file = os.getenv('OSM_OUTPUT_FILE', 'osm_data.rdf')
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate the configuration settings."""
        if not self.connection_string:
            logger.warning("No DGRAPH_CONNECTION_STRING provided. Using localhost:8080")
            self.connection_string = "@dgraph://localhost:8080"
        
        if not os.path.exists(self.data_dir):
            logger.info(f"Creating data directory: {self.data_dir}")
            os.makedirs(self.data_dir, exist_ok=True)
    
    def get_connection_params(self) -> dict:
        """Parse connection string and return connection parameters."""
        if self.connection_string.startswith('@'):
            # Local connection
            host_port = self.connection_string[1:].replace('dgraph://', '')
            return {
                'host': host_port.split(':')[0],
                'port': int(host_port.split(':')[1]) if ':' in host_port else 8080
            }
        else:
            # Remote connection (simplified parsing)
            logger.info("Remote Dgraph connection detected")
            return {
                'connection_string': self.connection_string
            }
    
    def get_osm_config(self) -> dict:
        """Get OSM-specific configuration."""
        return {
            'location': self.osm_location,
            'tags': self.osm_tags,
            'output_file': self.osm_output_file
        }
    
    def print_config(self):
        """Print current configuration."""
        print("🔧 OSM Dgraph Configuration")
        print("=" * 40)
        print(f"📊 Dgraph Connection: {self.connection_string}")
        print(f"📦 Batch Size: {self.batch_size}")
        print(f"📁 Data Directory: {self.data_dir}")
        print(f"🗺️  OSM Location: {self.osm_location}")
        print(f"🏷️  OSM Tags: {self.osm_tags}")
        print(f"💾 Output File: {self.osm_output_file}")
        print(f"📝 Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")


def main():
    """Main function to display configuration."""
    config = DgraphConfig()
    config.print_config()


if __name__ == "__main__":
    main()
