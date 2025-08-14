"""
Dgraph Configuration Module

Handles Dgraph connection string parsing and configuration management.
Supports both local and remote Dgraph instances with authentication.
"""

import os
import re
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

class DgraphConfig:
    """Configuration manager for Dgraph connections"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize configuration from file"""
        self.config_file = config_file
        self.connection_string = None
        self.host = None
        self.port = None
        self.ssl_mode = None
        self.bearer_token = None
        self.use_ssl = False
        
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
        self.connection_string = os.getenv('DGRAPH_CONNECTION_STRING')
        
        if not self.connection_string:
            # Default to localhost if no connection string provided
            self.connection_string = "@dgraph://localhost:8080"
            print(f"⚠️  No DGRAPH_CONNECTION_STRING found, using default: {self.connection_string}")
    
    def _parse_connection_string(self):
        """Parse Dgraph connection string format: @dgraph://host:port?param=value"""
        if not self.connection_string.startswith('@dgraph://'):
            raise ValueError("Invalid Dgraph connection string format. Must start with '@dgraph://'")
        
        # Remove the @dgraph:// prefix
        connection_url = self.connection_string[10:]
        
        # Parse the URL
        parsed = urlparse(f"dgraph://{connection_url}")
        
        self.host = parsed.hostname
        self.port = parsed.port or 443  # Default to 443 for HTTPS
        
        # Parse query parameters
        query_params = parse_qs(parsed.query)
        
        # SSL configuration
        self.ssl_mode = query_params.get('sslmode', ['disable'])[0]
        self.use_ssl = self.ssl_mode != 'disable'
        
        # Authentication
        self.bearer_token = query_params.get('bearertoken', [None])[0]
        
        # Additional parameters
        self.additional_params = {k: v[0] for k, v in query_params.items() 
                                if k not in ['sslmode', 'bearertoken']}
    
    def get_http_url(self) -> str:
        """Get HTTP URL for Dgraph HTTP API"""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.host}:{self.port}"
    
    def get_grpc_url(self) -> str:
        """Get gRPC URL for Dgraph gRPC API"""
        return f"{self.host}:{self.port}"
    
    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers including authentication"""
        headers = {'Content-Type': 'application/json'}
        
        if self.bearer_token:
            headers['Authorization'] = f'Bearer {self.bearer_token}'
        
        return headers
    
    def get_ssl_config(self) -> Dict[str, any]:
        """Get SSL configuration for requests"""
        if not self.use_ssl:
            return {}
        
        ssl_config = {}
        
        if self.ssl_mode == 'verify-ca':
            ssl_config['verify'] = True
        elif self.ssl_mode == 'require':
            ssl_config['verify'] = True
        elif self.ssl_mode == 'allow':
            ssl_config['verify'] = False
        elif self.ssl_mode == 'prefer':
            ssl_config['verify'] = True
        elif self.ssl_mode == 'disable':
            ssl_config['verify'] = False
        
        return ssl_config
    
    def validate_connection(self) -> bool:
        """Validate the connection configuration"""
        if not self.host:
            print("❌ Invalid host in connection string")
            return False
        
        if not self.port:
            print("❌ Invalid port in connection string")
            return False
        
        if self.use_ssl and not self.bearer_token:
            print("⚠️  SSL enabled but no bearer token provided")
        
        return True
    
    def print_config(self):
        """Print current configuration"""
        print("🔧 Dgraph Configuration:")
        print(f"  Host: {self.host}")
        print(f"  Port: {self.port}")
        print(f"  SSL Mode: {self.ssl_mode}")
        print(f"  Use SSL: {self.use_ssl}")
        print(f"  Bearer Token: {'***' if self.bearer_token else 'None'}")
        print(f"  HTTP URL: {self.get_http_url()}")
        print(f"  gRPC URL: {self.get_grpc_url()}")
        if self.additional_params:
            print(f"  Additional Params: {self.additional_params}")

def load_dgraph_config(config_file: str = "config.env") -> DgraphConfig:
    """Load Dgraph configuration from file"""
    return DgraphConfig(config_file)

# Example usage
if __name__ == "__main__":
    config = load_dgraph_config()
    config.print_config()
    
    if config.validate_connection():
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has issues")
