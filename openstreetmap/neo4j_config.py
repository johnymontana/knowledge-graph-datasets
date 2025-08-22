#!/usr/bin/env python3
"""
Neo4j Configuration Management for OSM Import

This module handles configuration loading and Neo4j connection setup
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


class Neo4jConfig:
    """Configuration class for Neo4j connection and import settings."""
    
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD', 'password')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')
        self.batch_size = int(os.getenv('BATCH_SIZE', '1000'))
        self.data_dir = os.getenv('DATA_DIR', 'data')
        
        # OSM-specific configuration
        self.osm_location = os.getenv('OSM_LOCATION', 'San Francisco, California')
        self.osm_tags = os.getenv('OSM_TAGS', 'amenity=restaurant')
        self.osm_output_file = os.getenv('OSM_OUTPUT_FILE', 'osm_data.cypher')
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate the configuration settings."""
        if not self.uri:
            logger.warning("No NEO4J_URI provided. Using bolt://localhost:7687")
            self.uri = "bolt://localhost:7687"
        
        if not os.path.exists(self.data_dir):
            logger.info(f"Creating data directory: {self.data_dir}")
            os.makedirs(self.data_dir, exist_ok=True)
    
    def get_connection_params(self) -> dict:
        """Get Neo4j connection parameters."""
        return {
            'uri': self.uri,
            'username': self.username,
            'password': self.password,
            'database': self.database
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
        print("🔧 OSM Neo4j Configuration")
        print("=" * 40)
        print(f"📊 Neo4j URI: {self.uri}")
        print(f"👤 Username: {self.username}")
        print(f"💽 Database: {self.database}")
        print(f"📦 Batch Size: {self.batch_size}")
        print(f"📁 Data Directory: {self.data_dir}")
        print(f"🗺️  OSM Location: {self.osm_location}")
        print(f"🏷️  OSM Tags: {self.osm_tags}")
        print(f"💾 Output File: {self.osm_output_file}")
        print(f"📝 Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")


def main():
    """Main function to display configuration."""
    config = Neo4jConfig()
    config.print_config()


if __name__ == "__main__":
    main()
