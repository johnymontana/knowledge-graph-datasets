#!/usr/bin/env python3
"""
Sample Neo4j Queries for Foursquare Transit and Places Data

This script demonstrates various queries for exploring the Foursquare dataset
with focus on geospatial analysis and routing possibilities.
"""

import sys
from pathlib import Path

# Add parent directory to path to import neo4j_config
sys.path.append(str(Path(__file__).parent.parent / 'gtfs'))
from neo4j_config import Neo4jConfig

from neo4j import GraphDatabase
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FoursquareQueryRunner:
    """Sample queries for Foursquare data"""
    
    def __init__(self, config: Neo4jConfig = None):
        if config is None:
            config = Neo4jConfig()
        
        self.config = config
        self.driver = GraphDatabase.driver(
            config.uri,
            auth=config.get_auth(),
            **config.get_driver_config()
        )
    
    def run_query(self, query: str, parameters: dict = None, description: str = ""):
        """Run a query and display results"""
        print(f"\n{'='*60}")
        print(f"Query: {description}")
        print(f"{'='*60}")
        print(f"Cypher: {query}")
        print("-" * 60)
        
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, parameters or {})
                
                records = list(result)
                if records:
                    for record in records[:10]:  # Limit to first 10 results
                        print(record)
                    
                    if len(records) > 10:
                        print(f"... and {len(records) - 10} more results")
                    
                    print(f"\nTotal results: {len(records)}")
                else:
                    print("No results found")
                    
        except Exception as e:
            print(f"Error executing query: {e}")
        
        print("-" * 60)
    
    def basic_data_exploration(self):
        """Basic queries to explore the dataset"""
        
        # Count nodes by type
        self.run_query(
            """
            MATCH (n)
            RETURN labels(n) as node_type, count(n) as count
            ORDER BY count DESC
            """,
            description="Count nodes by type"
        )
        
        # Sample transit stops
        self.run_query(
            """
            MATCH (ts:TransitStop)
            RETURN ts.stop_name, ts.stop_lat, ts.stop_lon, ts.zone_id
            ORDER BY ts.stop_name
            LIMIT 10
            """,
            description="Sample transit stops"
        )
        
        # Sample places with categories
        self.run_query(
            """
            MATCH (p:Place)-[:BELONGS_TO_CATEGORY]->(c:Category)
            RETURN p.name, p.locality, c.label, p.latitude, p.longitude
            ORDER BY p.name
            LIMIT 10
            """,
            description="Sample places with categories"
        )
        
        # Top categories by place count
        self.run_query(
            """
            MATCH (c:Category)<-[:BELONGS_TO_CATEGORY]-(p:Place)
            RETURN c.label, count(p) as place_count
            ORDER BY place_count DESC
            LIMIT 10
            """,
            description="Top categories by place count"
        )
    
    def geospatial_queries(self):
        """Geospatial analysis queries"""
        
        # Places within 500m of transit stops
        self.run_query(
            """
            MATCH (p:Place)-[:WITHIN_500M]->(ts:TransitStop)
            RETURN ts.stop_name, count(p) as nearby_places
            ORDER BY nearby_places DESC
            LIMIT 10
            """,
            description="Transit stops with most nearby places (within 500m)"
        )
        
        # Find places near a specific location using spatial distance
        self.run_query(
            """
            WITH point({latitude: 47.6062, longitude: -122.3321}) as downtown_seattle
            MATCH (p:Place)
            WHERE p.location IS NOT NULL
            WITH p, distance(p.location, downtown_seattle) as distance_meters
            WHERE distance_meters <= 1000
            RETURN p.name, p.locality, round(distance_meters) as distance_m
            ORDER BY distance_meters
            LIMIT 15
            """,
            description="Places within 1km of downtown Seattle"
        )
        
        # Places by locality with transit accessibility
        self.run_query(
            """
            MATCH (p:Place)-[:WITHIN_500M]->(ts:TransitStop)
            RETURN p.locality, count(DISTINCT p) as accessible_places, 
                   count(DISTINCT ts) as nearby_stops
            ORDER BY accessible_places DESC
            LIMIT 10
            """,
            description="Localities with best transit accessibility"
        )
        
        # Distance analysis between places and their closest stops
        self.run_query(
            """
            MATCH (p:Place)-[:WITHIN_500M]->(ts:TransitStop)
            WHERE p.location IS NOT NULL AND ts.location IS NOT NULL
            WITH p, ts, distance(p.location, ts.location) as distance_meters
            ORDER BY p.fsq_place_id, distance_meters
            WITH p, collect({stop: ts, distance: distance_meters})[0] as closest_stop
            RETURN p.name, p.locality, 
                   closest_stop.stop.stop_name as closest_stop_name,
                   round(closest_stop.distance) as distance_meters
            ORDER BY distance_meters
            LIMIT 15
            """,
            description="Places and their closest transit stops"
        )
    
    def routing_analysis(self):
        """Routing and connectivity analysis"""
        
        # Multi-modal routing: Places accessible from a transit stop
        self.run_query(
            """
            MATCH path = (start:TransitStop {stop_name: "3rd Ave & Pike St"})-[:WITHIN_500M|NEAR_STOP*1..2]-(p:Place)-[:BELONGS_TO_CATEGORY]->(c:Category)
            WHERE c.label CONTAINS "Restaurant" OR c.label CONTAINS "Food"
            RETURN p.name, p.locality, c.label, length(path) as hop_count
            ORDER BY hop_count, p.name
            LIMIT 15
            """,
            description="Restaurants accessible from 3rd Ave & Pike St transit stop"
        )
        
        # Find transit stops that connect different areas
        self.run_query(
            """
            MATCH (ts:TransitStop)-[:WITHIN_500M]-(p:Place)
            WITH ts, collect(DISTINCT p.locality) as connected_localities
            WHERE size(connected_localities) > 1
            RETURN ts.stop_name, ts.stop_lat, ts.stop_lon, 
                   connected_localities, size(connected_localities) as locality_count
            ORDER BY locality_count DESC
            LIMIT 10
            """,
            description="Transit stops connecting multiple localities"
        )
        
        # Places reachable within 2 transit stops (using graph traversal)
        self.run_query(
            """
            MATCH path = (start:TransitStop {stop_name: "Westlake Station"})-[:WITHIN_500M*1..4]-(p:Place)
            WHERE p.name IS NOT NULL
            WITH p, min(length(path)) as min_hops
            RETURN p.name, p.locality, min_hops
            ORDER BY min_hops, p.name
            LIMIT 20
            """,
            description="Places reachable from Westlake Station (within 4 hops)"
        )
    
    def business_intelligence_queries(self):
        """Business intelligence and analysis queries"""
        
        # Category distribution by locality
        self.run_query(
            """
            MATCH (p:Place)-[:BELONGS_TO_CATEGORY]->(c:Category)
            WHERE p.locality IS NOT NULL
            RETURN p.locality, c.label, count(p) as place_count
            ORDER BY p.locality, place_count DESC
            """,
            description="Category distribution by locality"
        )
        
        # Transit desert analysis: Areas with few transit options
        self.run_query(
            """
            MATCH (p:Place)
            OPTIONAL MATCH (p)-[:WITHIN_500M]->(ts:TransitStop)
            WITH p.locality as locality, p, count(ts) as stop_count
            WITH locality, count(p) as total_places, 
                 sum(CASE WHEN stop_count = 0 THEN 1 ELSE 0 END) as places_without_transit
            WHERE total_places >= 5
            RETURN locality, total_places, places_without_transit,
                   round(100.0 * places_without_transit / total_places) as percent_without_transit
            ORDER BY percent_without_transit DESC
            LIMIT 15
            """,
            description="Transit desert analysis by locality"
        )
        
        # Most connected places (transit accessibility hubs)
        self.run_query(
            """
            MATCH (p:Place)-[:WITHIN_500M]->(ts:TransitStop)
            WITH p, count(DISTINCT ts) as transit_connections
            ORDER BY transit_connections DESC
            RETURN p.name, p.locality, p.latitude, p.longitude, 
                   transit_connections
            LIMIT 15
            """,
            description="Places with best transit connectivity"
        )
        
        # Service gaps: Categories with poor transit access
        self.run_query(
            """
            MATCH (c:Category)<-[:BELONGS_TO_CATEGORY]-(p:Place)
            OPTIONAL MATCH (p)-[:WITHIN_500M]->(ts:TransitStop)
            WITH c, count(p) as total_places, count(ts) as transit_connections
            WHERE total_places >= 5
            WITH c, total_places, transit_connections,
                 round(100.0 * transit_connections / total_places) as transit_coverage_percent
            RETURN c.label, total_places, transit_connections, transit_coverage_percent
            ORDER BY transit_coverage_percent
            LIMIT 15
            """,
            description="Categories with lowest transit coverage"
        )
    
    def advanced_spatial_queries(self):
        """Advanced spatial analysis queries"""
        
        # Cluster analysis: Find dense areas of places
        self.run_query(
            """
            MATCH (p1:Place)-[:WITHIN_500M]->(ts:TransitStop)<-[:WITHIN_500M]-(p2:Place)
            WHERE p1 <> p2
            WITH ts, collect(DISTINCT p1) + collect(DISTINCT p2) as connected_places
            RETURN ts.stop_name, ts.locality, size(connected_places) as cluster_size,
                   ts.stop_lat, ts.stop_lon
            ORDER BY cluster_size DESC
            LIMIT 10
            """,
            description="Transit stops creating largest place clusters"
        )
        
        # Spatial corridor analysis: Places along transit lines
        self.run_query(
            """
            MATCH (ts1:TransitStop)-[:WITHIN_500M]-(p:Place)-[:WITHIN_500M]-(ts2:TransitStop)
            WHERE ts1 <> ts2 AND ts1.locality = ts2.locality
            WITH p, count(DISTINCT ts1) + count(DISTINCT ts2) as corridor_connections
            RETURN p.name, p.locality, corridor_connections
            ORDER BY corridor_connections DESC
            LIMIT 15
            """,
            description="Places along transit corridors"
        )
        
        # Walkability index: Places within walking distance of multiple amenities
        self.run_query(
            """
            MATCH (p:Place)
            OPTIONAL MATCH (p)-[:WITHIN_500M]-(neighbor:Place)-[:BELONGS_TO_CATEGORY]->(c:Category)
            WHERE c.label CONTAINS "Restaurant" OR c.label CONTAINS "Shop" OR c.label CONTAINS "Service"
            WITH p, count(DISTINCT neighbor) as amenity_count
            WHERE amenity_count > 0
            RETURN p.name, p.locality, amenity_count
            ORDER BY amenity_count DESC
            LIMIT 15
            """,
            description="Places with highest walkability (nearby amenities)"
        )
    
    def run_all_samples(self):
        """Run all sample queries"""
        print("FOURSQUARE DATA EXPLORATION - SAMPLE QUERIES")
        print("="*80)
        
        print("\n\n1. BASIC DATA EXPLORATION")
        self.basic_data_exploration()
        
        print("\n\n2. GEOSPATIAL QUERIES")
        self.geospatial_queries()
        
        print("\n\n3. ROUTING ANALYSIS")
        self.routing_analysis()
        
        print("\n\n4. BUSINESS INTELLIGENCE")
        self.business_intelligence_queries()
        
        print("\n\n5. ADVANCED SPATIAL ANALYSIS")
        self.advanced_spatial_queries()
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()

def main():
    """Main function to run sample queries"""
    try:
        # Load configuration
        config = Neo4jConfig()
        
        # Create query runner
        query_runner = FoursquareQueryRunner(config)
        
        try:
            # Run all sample queries
            query_runner.run_all_samples()
            
        finally:
            query_runner.close()
            
    except Exception as e:
        logger.error(f"Error running queries: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()