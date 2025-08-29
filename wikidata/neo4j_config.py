#!/usr/bin/env python3
"""
Neo4j Configuration for Wikidata Import

This module provides configuration management for Neo4j database connections
and Wikidata import settings.
"""

import os
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

class Neo4jConfig:
    """Configuration class for Neo4j database connection"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize configuration from environment file"""
        # Load environment variables from config file
        config_path = Path(config_file)
        if config_path.exists():
            load_dotenv(config_path)
        else:
            logger.warning(f"Config file {config_file} not found, using environment variables")
        
        # Neo4j connection settings
        self.uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD', 'password')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')
        
        # Import settings
        self.batch_size = int(os.getenv('BATCH_SIZE', '1000'))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.data_dir = Path(os.getenv('DATA_DIR', 'data'))
        
        # Wikidata SPARQL settings
        self.wikidata_endpoint = os.getenv('WIKIDATA_ENDPOINT', 'https://query.wikidata.org/sparql')
        self.request_delay = float(os.getenv('REQUEST_DELAY', '1.0'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.timeout = int(os.getenv('TIMEOUT', '30'))
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(level=getattr(logging, self.log_level))
        
    def get_driver(self):
        """Create and return Neo4j driver"""
        return GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password)
        )
    
    def get_database(self) -> str:
        """Get database name"""
        return self.database
    
    def validate_connection(self) -> bool:
        """Test Neo4j connection"""
        try:
            with self.get_driver() as driver:
                with driver.session(database=self.database) as session:
                    result = session.run("RETURN 1 as test")
                    return result.single()["test"] == 1
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            return False
    
    def __str__(self):
        """String representation of config"""
        return f"""Neo4jConfig(
    uri={self.uri},
    database={self.database},
    batch_size={self.batch_size},
    wikidata_endpoint={self.wikidata_endpoint}
)"""

def load_neo4j_config(config_file: str = "config.env") -> Neo4jConfig:
    """Load Neo4j configuration"""
    return Neo4jConfig(config_file)