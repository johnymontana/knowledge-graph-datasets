"""
Neo4j Configuration Module

Handles Neo4j connection string parsing and configuration management.
Supports both local and remote Neo4j instances with authentication.
"""

import os
import re
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

class Neo4jConfig:
    """Configuration manager for Neo4j connections"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize configuration from file"""
        self.config_file = config_file
        self.connection_string = None
        self.uri = None
        self.host = None
        self.port = None
        self.username = None
        self.password = None
        self.database = None
        self.encrypted = True
        self.trust = None
        
        # Load configuration
        self._load_config()
        self._parse_connection_string()
    
    def _load_config(self):
        """Load configuration from environment file"""
        # Try to load from config.env first
        if os.path.exists(self.config_file):
            load_dotenv(self.config_file)
        else:
            # Fall back to .env if config.env doesn't exist
            load_dotenv()
        
        # Get connection string from environment
        self.connection_string = os.getenv('NEO4J_CONNECTION_STRING') or os.getenv('NEO4J_URI')
        
        if not self.connection_string:
            # Default to localhost if no connection string provided
            self.connection_string = "bolt://localhost:7687"
            print(f"⚠️  No NEO4J_CONNECTION_STRING found, using default: {self.connection_string}")
    
    def _parse_connection_string(self):
        """Parse Neo4j connection string format: bolt://username:password@host:port/database?param=value"""
        try:
            parsed = urlparse(self.connection_string)
            
            # Extract scheme (bolt, neo4j, etc.)
            self.scheme = parsed.scheme or 'bolt'
            
            # Extract host and port
            self.host = parsed.hostname or 'localhost'
            self.port = parsed.port or (7687 if self.scheme == 'bolt' else 7474)
            
            # Extract credentials
            self.username = parsed.username or os.getenv('NEO4J_USERNAME', 'neo4j')
            self.password = parsed.password or os.getenv('NEO4J_PASSWORD', 'password')
            
            # Extract database
            self.database = parsed.path.lstrip('/') if parsed.path else os.getenv('NEO4J_DATABASE', 'neo4j')
            
            # Build URI
            self.uri = f"{self.scheme}://{self.host}:{self.port}"
            
            # Parse query parameters
            query_params = parse_qs(parsed.query)
            
            # SSL/Encryption configuration
            self.encrypted = query_params.get('encrypted', ['true'])[0].lower() == 'true'
            self.trust = query_params.get('trust', [None])[0]
            
            # Additional parameters
            self.additional_params = {k: v[0] for k, v in query_params.items() 
                                    if k not in ['encrypted', 'trust']}
                                    
        except Exception as e:
            raise ValueError(f"Invalid Neo4j connection string format: {e}")
    
    def get_driver_config(self) -> Dict[str, any]:
        """Get Neo4j driver configuration"""
        config = {
            'encrypted': self.encrypted,
            'trust': self.trust or 'TRUST_SYSTEM_CA_SIGNED_CERTIFICATES'
        }
        
        # Remove None values
        return {k: v for k, v in config.items() if v is not None}
    
    def get_auth(self) -> Tuple[str, str]:
        """Get authentication tuple for Neo4j driver"""
        return (self.username, self.password)
    
    def validate_connection(self) -> bool:
        """Validate the connection configuration"""
        if not self.host:
            print("❌ Invalid host in connection string")
            return False
        
        if not self.port:
            print("❌ Invalid port in connection string")
            return False
            
        if not self.username:
            print("❌ No username provided")
            return False
            
        if not self.password:
            print("❌ No password provided")
            return False
        
        return True
    
    def print_config(self):
        """Print current configuration"""
        print("🔧 Neo4j Configuration:")
        print(f"  URI: {self.uri}")
        print(f"  Host: {self.host}")
        print(f"  Port: {self.port}")
        print(f"  Database: {self.database}")
        print(f"  Username: {self.username}")
        print(f"  Password: {'***' if self.password else 'None'}")
        print(f"  Encrypted: {self.encrypted}")
        print(f"  Trust: {self.trust}")
        if self.additional_params:
            print(f"  Additional Params: {self.additional_params}")

def load_neo4j_config(config_file: str = "config.env") -> Neo4jConfig:
    """Load Neo4j configuration from file"""
    return Neo4jConfig(config_file)

# Example usage
if __name__ == "__main__":
    config = load_neo4j_config()
    config.print_config()
    
    if config.validate_connection():
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has issues")