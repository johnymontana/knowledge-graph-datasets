#!/usr/bin/env python3
"""
Test Dgraph Connection Script

This script tests different Dgraph endpoints to understand the connection structure.
"""

import requests
import json
from dgraph_config import DgraphConfig

def test_endpoints(config):
    """Test different Dgraph endpoints"""
    print(f"Testing connection to: {config.get_http_url()}")
    print(f"Headers: {config.get_headers()}")
    print(f"SSL Config: {config.get_ssl_config()}")
    print()
    
    # Test different endpoints
    endpoints = [
        "/health",
        "/query", 
        "/mutate",
        "/alter",
        "/graphql",
        "/admin",
        "/",
    ]
    
    for endpoint in endpoints:
        url = f"{config.get_http_url()}{endpoint}"
        print(f"Testing {endpoint}:")
        
        try:
            if endpoint == "/query":
                # Test POST to query endpoint
                response = requests.post(
                    url,
                    headers=config.get_headers(),
                    json={"query": "{}"},
                    verify=config.get_ssl_config().get('verify', True),
                    timeout=10
                )
            elif endpoint == "/graphql":
                # Test POST to GraphQL endpoint
                response = requests.post(
                    url,
                    headers=config.get_headers(),
                    json={"query": "query { __schema { types { name } } }"},
                    verify=config.get_ssl_config().get('verify', True),
                    timeout=10
                )
            else:
                # Test GET to other endpoints
                response = requests.get(
                    url,
                    headers=config.get_headers(),
                    verify=config.get_ssl_config().get('verify', True),
                    timeout=10
                )
            
            print(f"  Status: {response.status_code}")
            print(f"  Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print(f"  Response: {response.text[:200]}...")
            elif response.status_code == 400:
                print(f"  Response: {response.text[:200]}...")
            else:
                print(f"  Response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  Error: {e}")
        
        print()

def main():
    """Main function"""
    try:
        config = DgraphConfig()
        config.print_config()
        print()
        
        if not config.validate_connection():
            print("❌ Configuration validation failed")
            return
        
        test_endpoints(config)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
