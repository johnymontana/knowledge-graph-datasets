#!/usr/bin/env python3
"""
Sample Queries for OSM Data in Neo4j

This script provides example queries for exploring OpenStreetMap data
that has been imported into Neo4j. It demonstrates various types of
spatial and attribute-based queries using Cypher.
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, List
from neo4j import GraphDatabase
from neo4j_config import Neo4jConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OSMQueryExamples:
    """Class containing sample queries for OSM data in Neo4j."""
    
    def __init__(self, config: Neo4jConfig):
        self.config = config
        self.driver = None
        self._setup_neo4j()
    
    def _setup_neo4j(self):
        """Setup Neo4j driver connection."""
        try:
            conn_params = self.config.get_connection_params()
            self.driver = GraphDatabase.driver(
                conn_params['uri'],
                auth=(conn_params['username'], conn_params['password'])
            )
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("✅ Connected to Neo4j")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def __del__(self):
        """Close Neo4j driver on cleanup."""
        if self.driver:
            self.driver.close()
    
    def query_amenities_by_type(self, amenity_type: str) -> Dict[str, Any]:
        """Query for amenities of a specific type."""
        query = """
        MATCH (f:Feature)-[:HAS_GEOMETRY]->(g:Geometry)
        WHERE f.amenity = $amenity_type
        RETURN f.name as name, f.amenity as amenity, g.wkt as geometry, f.address as address
        LIMIT 100
        """
        
        try:
            if self.driver:
                with self.driver.session() as session:
                    result = session.run(query, amenity_type=amenity_type)
                    records = list(result)
                    return {"records": [dict(record) for record in records]}
            else:
                logger.warning("⚠️  Neo4j driver not available, showing query structure")
                return {"query": query, "parameters": {"amenity_type": amenity_type}}
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return {"error": str(e)}
    
    def query_features_by_location(self, location_name: str) -> Dict[str, Any]:
        """Query for features in a specific location."""
        query = """
        MATCH (f:Feature)-[:HAS_GEOMETRY]->(g:Geometry)
        WHERE toLower(f.name) CONTAINS toLower($location)
        RETURN f.name as name, f.amenity as amenity, g.wkt as geometry, f.address as address
        LIMIT 100
        """
        
        try:
            if self.driver:
                with self.driver.session() as session:
                    result = session.run(query, location=location_name)
                    records = list(result)
                    return {"records": [dict(record) for record in records]}
            else:
                logger.warning("⚠️  Neo4j driver not available, showing query structure")
                return {"query": query, "parameters": {"location": location_name}}
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return {"error": str(e)}
    
    def query_spatial_features(self, bbox: List[float]) -> Dict[str, Any]:
        """Query for features within a bounding box."""
        # This uses point distance for spatial filtering
        query = """
        MATCH (f:Feature)-[:HAS_GEOMETRY]->(g:Geometry)
        WHERE g.wkt IS NOT NULL
        RETURN f.name as name, f.amenity as amenity, g.wkt as geometry
        LIMIT 50
        """
        
        try:
            if self.driver:
                with self.driver.session() as session:
                    result = session.run(query)
                    records = list(result)
                    return {"records": [dict(record) for record in records]}
            else:
                logger.warning("⚠️  Neo4j driver not available, showing query structure")
                return {"query": query, "parameters": {"bbox": bbox}}
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return {"error": str(e)}
    
    def query_feature_relationships(self, feature_name: str) -> Dict[str, Any]:
        """Query for relationships of a specific feature."""
        query = """
        MATCH (f:Feature {name: $feature_name})-[:HAS_GEOMETRY]->(g:Geometry)
        OPTIONAL MATCH (f)-[r]-(related)
        RETURN f.name as name, f.amenity as amenity, g.wkt as geometry, f.address as address,
               type(r) as relationship_type, related.name as related_name
        """
        
        try:
            if self.driver:
                with self.driver.session() as session:
                    result = session.run(query, feature_name=feature_name)
                    records = list(result)
                    return {"records": [dict(record) for record in records]}
            else:
                logger.warning("⚠️  Neo4j driver not available, showing query structure")
                return {"query": query, "parameters": {"feature_name": feature_name}}
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
        result = self.query_features_by_location("Francisco")
        self._display_query_result("San Francisco Features", result)
        
        # Query 3: Spatial query example
        logger.info("\n3️⃣  Spatial query example...")
        bbox = [-122.5, 37.7, -122.4, 37.8]  # San Francisco area
        result = self.query_spatial_features(bbox)
        self._display_query_result("Spatial Features", result)
        
        # Query 4: Feature relationships
        logger.info("\n4️⃣  Feature relationships example...")
        result = self.query_feature_relationships("Sample Restaurant")
        self._display_query_result("Feature Relationships", result)
        
        logger.info("\n🎉 Sample queries completed!")
    
    def _display_query_result(self, title: str, result: Dict[str, Any]):
        """Display query results in a formatted way."""
        print(f"\n📊 {title}")
        print("=" * 50)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        elif "query" in result:
            print("📝 Query Structure (Neo4j not connected):")
            print(f"Query: {result['query']}")
            print(f"Parameters: {result.get('parameters', {})}")
        else:
            # Display actual results
            print("✅ Query executed successfully")
            if "records" in result:
                records = result["records"]
                print(f"Found {len(records)} results:")
                for i, record in enumerate(records[:5]):  # Show first 5 results
                    print(f"  {i+1}. {record}")
                if len(records) > 5:
                    print(f"  ... and {len(records) - 5} more")
            else:
                print(f"Result: {result}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run sample queries on OSM data in Neo4j")
    parser.add_argument("--amenity", help="Query for specific amenity type")
    parser.add_argument("--location", help="Query for specific location")
    parser.add_argument("--spatial", help="Spatial query with bounding box (x1,y1,x2,y2)")
    parser.add_argument("--feature", help="Query for specific feature name")
    parser.add_argument("--all", action="store_true", help="Run all sample queries")
    
    args = parser.parse_args()
    
    # Load configuration
    config = Neo4jConfig()
    
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
