#!/usr/bin/env python3
"""
Simple test script to verify Dgraph connection
"""

import pydgraph
from dgraph_config import DgraphConfig

def main():
    print("🔧 Testing Dgraph Connection...")
    
    try:
        # Load configuration
        config = DgraphConfig()
        config.print_config()
        
        # Create pydgraph client
        client = pydgraph.open(config.connection_string)
        print("✅ pydgraph client created successfully")
        
        # Test with a simple query
        txn = client.txn()
        try:
            # Use a valid DQL query
            response = txn.query("query { }")
            print("✅ Query executed successfully")
            print(f"Response type: {type(response)}")
            print(f"Response: {response}")
        finally:
            txn.discard()
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

