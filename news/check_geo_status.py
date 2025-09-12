#!/usr/bin/env python3
"""
Script to check the status of Geo nodes in Neo4j.
Shows count of nodes with/without location properties.
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from neo4j import GraphDatabase
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure you have installed the required dependencies:")
    print("  pip install neo4j python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

def check_geo_status():
    """Check the status of Geo nodes in Neo4j."""
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password')
    database = os.getenv('NEO4J_DATABASE', 'neo4j')
    
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session(database=database) as session:
            # Count total Geo nodes
            total_result = session.run('MATCH (g:Geo) RETURN count(g) as total')
            total = total_result.single()['total']
            
            # Count Geo nodes with location
            with_location_result = session.run('MATCH (g:Geo) WHERE g.location IS NOT NULL RETURN count(g) as count')
            with_location = with_location_result.single()['count']
            
            # Count Geo nodes without location
            without_location = total - with_location
            
            print(f'🌍 Geo Nodes Status:')
            print(f'  📊 Total: {total}')
            print(f'  ✅ With location: {with_location}')
            print(f'  ❌ Without location: {without_location}')
            if total > 0:
                completion = (with_location / total) * 100
                print(f'  📈 Completion: {completion:.1f}%')
            else:
                print(f'  📈 Completion: 0%')
        
        driver.close()
        
    except Exception as e:
        print(f"❌ Error checking Geo status: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_geo_status()
