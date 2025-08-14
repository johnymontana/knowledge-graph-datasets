#!/usr/bin/env python3
"""
Sample Queries for OSM Data in Dgraph

This script provides example queries for exploring OpenStreetMap data
that has been imported into Dgraph. It demonstrates various types of
spatial and attribute-based queries.
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, List
import pydgraph
from dgraph_config import DgraphConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OSMQueryExamples:
    """Class containing sample queries for OSM data in Dgraph."""
    
    def __init__(self, config: DgraphConfig):
        self.config = config
        self.dgraph_client = None
        self._setup_dgraph()
    
    def _setup_dgraph(self):
        """Setup Dgraph client connection."""
        try:
            conn_params = self.config.get_connection_params()
            if 'connection_string' in conn_params:
                # Remote connection
                self.dgraph_client = pydgraph.DgraphClient(
                    pydgraph.DgraphClientStub.from_spec(conn_params['connection_string'])
                )
            else:
                # Local connection
                self.dgraph_client = pydgraph.DgraphClient(
                    pydgraph.DgraphClientStub(conn_params['host'], conn_params['port'])
                )
            logger.info("✅ Connected to Dgraph")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Dgraph: {e}")
            self.dgraph_client = None
    
    def query_amenities_by_type(self, amenity_type: str) -> Dict[str, Any]:
        """Query for amenities of a specific type."""
        query = """
        query amenities($type: string) {
            amenities(func: eq(amenity, $type)) {
                uid
                name
                amenity
                geometry {
                    wkt
                }
                address
            }
        }
        """
        
        variables = {"$type": amenity_type}
        
        try:
            if self.dgraph_client:
                result = self.dgraph_client.txn(read_only=True).query(query, variables=variables)
                return result
            else:
                logger.warning("⚠️  Dgraph client not available, showing query structure")
                return {"query": query, "variables": variables}
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return {"error": str(e)}
    
    def query_features_by_location(self, location_name: str) -> Dict[str, Any]:
        """Query for features in a specific location."""
        query = """
        query location_features($location: string) {
            features(func: eq(location, $location)) {
                uid
                name
                amenity
                geometry {
                    wkt
                }
                address
            }
        }
        """
        
        variables = {"$location": location_name}
        
        try:
            if self.dgraph_client:
                result = self.dgraph_client.txn(read_only=True).query(query, variables=variables)
                return result
            else:
                logger.warning("⚠️  Dgraph client not available, showing query structure")
                return {"query": query, "variables": variables}
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return {"error": str(e)}
    
    def query_spatial_features(self, bbox: List[float]) -> Dict[str, Any]:
        """Query for features within a bounding box."""
        # This is a simplified example - real spatial queries would use Dgraph's spatial functions
        query = """
        query spatial_features($bbox: string) {
            features(func: has(geometry)) @filter(ge(geometry, $bbox)) {
                uid
                name
                amenity
                geometry {
                    wkt
                }
            }
        }
        """
        
        variables = {"$bbox": str(bbox)}
        
        try:
            if self.dgraph_client:
                result = self.dgraph_client.txn(read_only=True).query(query, variables=variables)
                return result
            else:
                logger.warning("⚠️  Dgraph client not available, showing query structure")
                return {"query": query, "variables": variables}
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return {"error": str(e)}
    
    def query_feature_relationships(self, feature_id: str) -> Dict[str, Any]:
        """Query for relationships of a specific feature."""
        query = """
        query feature_relationships($id: string) {
            feature(func: uid($id)) {
                uid
                name
                amenity
                geometry {
                    wkt
                }
                address
                ~location {
                    uid
                    name
                }
            }
        }
        """
        
        variables = {"$id": feature_id}
        
        try:
            if self.dgraph_client:
                result = self.dgraph_client.txn(read_only=True).query(query, variables=variables)
                return result
            else:
                logger.warning("⚠️  Dgraph client not available, showing query structure")
                return {"query": query, "variables": variables}
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return {"error": str(e)}
    
    def run_sample_queries(self):
        """Run a series of sample queries."""
        logger.info("🚀 Running sample OSM queries...")
        
        # Query 1: Restaurants
        logger.info("\n1️⃣  Querying for restaurants...")
        result = self.query_amenities_by_type("restaurant")
        self._display_query_result("Restaurants", result)
        
        # Query 2: Features in San Francisco
        logger.info("\n2️⃣  Querying for features in San Francisco...")
        result = self.query_features_by_location("San Francisco")
        self._display_query_result("San Francisco Features", result)
        
        # Query 3: Spatial query example
        logger.info("\n3️⃣  Spatial query example...")
        bbox = [-122.5, 37.7, -122.4, 37.8]  # San Francisco area
        result = self.query_spatial_features(bbox)
        self._display_query_result("Spatial Features", result)
        
        # Query 4: Feature relationships
        logger.info("\n4️⃣  Feature relationships example...")
        result = self.query_feature_relationships("example_uid")
        self._display_query_result("Feature Relationships", result)
        
        logger.info("\n🎉 Sample queries completed!")
    
    def _display_query_result(self, title: str, result: Dict[str, Any]):
        """Display query results in a formatted way."""
        print(f"\n📊 {title}")
        print("=" * 50)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        elif "query" in result:
            print("📝 Query Structure (Dgraph not connected):")
            print(f"Query: {result['query']}")
            print(f"Variables: {result['variables']}")
        else:
            # Display actual results
            print("✅ Query executed successfully")
            if hasattr(result, 'json'):
                print(f"Raw result: {result.json()}")
            else:
                print(f"Result: {result}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run sample queries on OSM data in Dgraph")
    parser.add_argument("--amenity", help="Query for specific amenity type")
    parser.add_argument("--location", help="Query for specific location")
    parser.add_argument("--spatial", help="Spatial query with bounding box (x1,y1,x2,y2)")
    parser.add_argument("--feature", help="Query for specific feature ID")
    parser.add_argument("--all", action="store_true", help="Run all sample queries")
    
    args = parser.parse_args()
    
    # Load configuration
    config = DgraphConfig()
    
    # Create query examples
    query_examples = OSMQueryExamples(config)
    
    if args.amenity:
        # Single amenity query
        result = query_examples.query_amenities_by_type(args.amenity)
        query_examples._display_query_result(f"Amenities: {args.amenity}", result)
    elif args.location:
        # Single location query
        result = query_examples.query_features_by_location(args.location)
        query_examples._display_query_result(f"Location: {args.location}", result)
    elif args.spatial:
        # Single spatial query
        try:
            bbox = [float(x) for x in args.spatial.split(',')]
            if len(bbox) != 4:
                raise ValueError("Bounding box must have 4 coordinates")
            result = query_examples.query_spatial_features(bbox)
            query_examples._display_query_result(f"Spatial Query: {bbox}", result)
        except ValueError as e:
            logger.error(f"Invalid bounding box format: {e}")
            sys.exit(1)
    elif args.feature:
        # Single feature query
        result = query_examples.query_feature_relationships(args.feature)
        query_examples._display_query_result(f"Feature: {args.feature}", result)
    elif args.all:
        # Run all sample queries
        query_examples.run_sample_queries()
    else:
        # Default: run all sample queries
        query_examples.run_sample_queries()


if __name__ == "__main__":
    main()
