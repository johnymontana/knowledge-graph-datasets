#!/usr/bin/env python3
"""
Script to geocode Geo nodes in Neo4j that don't have a location property.
Uses the geocode_ollama module to convert location names to coordinates.
"""

import os
import sys
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from neo4j import GraphDatabase
    from data.articles.geocode_ollama import get_coordinates_from_ollama
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure you have installed the required dependencies:")
    print("  pip install neo4j python-dotenv requests")
    sys.exit(1)

# Load environment variables
load_dotenv()

class Neo4jGeocoder:
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD', 'password')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # Test connection
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1")
            print(f"✅ Connected to Neo4j at {self.uri}")
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            sys.exit(1)

    def close(self):
        if hasattr(self, 'driver'):
            self.driver.close()

    def find_geo_nodes_without_location(self) -> List[Dict[str, Any]]:
        """Find all Geo nodes that don't have a location property."""
        with self.driver.session(database=self.database) as session:
            query = """
            MATCH (g:Geo)
            WHERE g.location IS NULL
            RETURN g.name as name, id(g) as id
            ORDER BY g.name
            """
            result = session.run(query)
            nodes = [{"id": record["id"], "name": record["name"]} for record in result]
            return nodes

    def update_geo_node_location(self, node_id: int, latitude: float, longitude: float):
        """Update a Geo node with location coordinates."""
        with self.driver.session(database=self.database) as session:
            query = """
            MATCH (g:Geo)
            WHERE id(g) = $node_id
            SET g.location = point({latitude: $latitude, longitude: $longitude})
            RETURN g.name as name
            """
            result = session.run(query, node_id=node_id, latitude=latitude, longitude=longitude)
            record = result.single()
            return record["name"] if record else None

    def geocode_geo_nodes(self, batch_size: int = 10, delay: float = 1.0):
        """Geocode all Geo nodes without location properties."""
        nodes = self.find_geo_nodes_without_location()
        
        if not nodes:
            print("✅ All Geo nodes already have location properties!")
            return
        
        print(f"🌍 Found {len(nodes)} Geo nodes without location properties")
        print("Starting geocoding process...")
        
        successful = 0
        failed = 0
        
        for i, node in enumerate(nodes, 1):
            print(f"\n[{i}/{len(nodes)}] Geocoding: {node['name']}")
            
            try:
                # Get coordinates from Ollama
                latitude, longitude = get_coordinates_from_ollama(node['name'])
                
                # Update the node in Neo4j
                updated_name = self.update_geo_node_location(node['id'], latitude, longitude)
                
                if updated_name:
                    print(f"  ✅ Updated {updated_name}: {latitude:.6f}, {longitude:.6f}")
                    successful += 1
                else:
                    print(f"  ❌ Failed to update node in database")
                    failed += 1
                
                # Add delay to avoid overwhelming the Ollama API
                if i < len(nodes):
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"  ❌ Error geocoding '{node['name']}': {e}")
                failed += 1
                
                # Continue with next node even if this one fails
                continue
        
        print(f"\n🎉 Geocoding complete!")
        print(f"  ✅ Successful: {successful}")
        print(f"  ❌ Failed: {failed}")
        print(f"  📊 Total processed: {len(nodes)}")

def main():
    print("🌍 Neo4j Geo Node Geocoder")
    print("=" * 40)
    
    # Check if Ollama is running
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            raise Exception("Ollama API not responding")
        print("✅ Ollama is running")
    except Exception as e:
        print(f"❌ Ollama is not running or not accessible: {e}")
        print("Please start Ollama first: ollama serve")
        sys.exit(1)
    
    geocoder = Neo4jGeocoder()
    
    try:
        # Get command line arguments
        batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
        delay = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
        
        print(f"📋 Configuration:")
        print(f"  Batch size: {batch_size}")
        print(f"  Delay between requests: {delay}s")
        print()
        
        geocoder.geocode_geo_nodes(batch_size=batch_size, delay=delay)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Geocoding interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        geocoder.close()

if __name__ == "__main__":
    main()
