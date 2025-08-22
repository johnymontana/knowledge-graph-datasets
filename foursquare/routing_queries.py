#!/usr/bin/env python3
"""
Advanced Routing Queries for Foursquare Transit Data

This script demonstrates advanced routing and pathfinding capabilities
using Neo4j graph algorithms and geospatial functions.
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

class RoutingAnalysis:
    """Advanced routing and pathfinding analysis"""
    
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
        print(f"\n{'='*70}")
        print(f"Routing Query: {description}")
        print(f"{'='*70}")
        print(f"Cypher: {query}")
        print("-" * 70)
        
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, parameters or {})
                
                records = list(result)
                if records:
                    for record in records[:15]:  # Limit to first 15 results
                        print(record)
                    
                    if len(records) > 15:
                        print(f"... and {len(records) - 15} more results")
                    
                    print(f"\nTotal results: {len(records)}")
                else:
                    print("No results found")
                    
        except Exception as e:
            print(f"Error executing query: {e}")
        
        print("-" * 70)
    
    def shortest_path_analysis(self):
        """Shortest path routing between locations"""
        
        # Shortest path between two transit stops via places
        self.run_query(
            """
            MATCH start = (s1:TransitStop {stop_name: "3rd Ave & Pike St"})
            MATCH end = (s2:TransitStop {stop_name: "Westlake Station"})
            MATCH path = shortestPath((start)-[:WITHIN_500M*1..8]-(end))
            RETURN path, length(path) as path_length,
                   [n in nodes(path) | n.stop_name + " / " + n.name][0..10] as route_description
            ORDER BY path_length
            LIMIT 5
            """,
            description="Shortest path between Pike St and Westlake via places"
        )
        
        # Multi-modal shortest path: transit stop -> restaurant
        self.run_query(
            """
            MATCH start = (ts:TransitStop {stop_name: "University District Station"})
            MATCH (restaurant:Place)-[:BELONGS_TO_CATEGORY]->(c:Category)
            WHERE c.label CONTAINS "Restaurant"
            MATCH path = shortestPath((start)-[:WITHIN_500M*1..6]-(restaurant))
            WITH restaurant, path, length(path) as distance
            ORDER BY distance, restaurant.name
            RETURN restaurant.name, restaurant.address, distance,
                   [n in nodes(path) WHERE n:TransitStop | n.stop_name] as transit_stops_used
            LIMIT 10
            """,
            description="Closest restaurants from University District Station"
        )
    
    def accessibility_analysis(self):
        """Transit accessibility and service area analysis"""
        
        # Service area: all places reachable within N hops from a transit stop
        self.run_query(
            """
            MATCH (start:TransitStop {stop_name: "Capitol Hill Station"})
            MATCH path = (start)-[:WITHIN_500M*1..4]-(reachable:Place)
            WITH reachable, min(length(path)) as min_hops
            MATCH (reachable)-[:BELONGS_TO_CATEGORY]->(c:Category)
            RETURN c.label as category, count(reachable) as reachable_places, 
                   round(avg(min_hops), 1) as avg_hops
            ORDER BY reachable_places DESC
            LIMIT 15
            """,
            description="Service area from Capitol Hill Station (by category)"
        )
        
        # Transit coverage analysis: percentage of places reachable
        self.run_query(
            """
            MATCH (p:Place)
            OPTIONAL MATCH path = shortestPath((ts:TransitStop)-[:WITHIN_500M*1..6]-(p))
            WITH p, 
                 CASE WHEN path IS NOT NULL THEN length(path) ELSE null END as accessibility_hops,
                 CASE WHEN path IS NOT NULL THEN true ELSE false END as is_accessible
            MATCH (p)-[:BELONGS_TO_CATEGORY]->(c:Category)
            WITH c.label as category, 
                 count(p) as total_places,
                 sum(CASE WHEN is_accessible THEN 1 ELSE 0 END) as accessible_places,
                 avg(accessibility_hops) as avg_accessibility_hops
            WHERE total_places >= 5
            RETURN category, total_places, accessible_places,
                   round(100.0 * accessible_places / total_places, 1) as accessibility_percent,
                   round(avg_accessibility_hops, 1) as avg_hops
            ORDER BY accessibility_percent DESC
            LIMIT 15
            """,
            description="Transit accessibility by place category"
        )
        
        # Find transit gaps: places with poor accessibility
        self.run_query(
            """
            MATCH (p:Place)
            OPTIONAL MATCH path = shortestPath((ts:TransitStop)-[:WITHIN_500M*1..8]-(p))
            WHERE path IS NULL
            MATCH (p)-[:BELONGS_TO_CATEGORY]->(c:Category)
            RETURN p.name, p.address, p.locality, c.label,
                   p.latitude, p.longitude
            ORDER BY p.locality, p.name
            LIMIT 20
            """,
            description="Places with no transit accessibility (transit gaps)"
        )
    
    def multi_modal_routing(self):
        """Multi-modal routing combining transit and walking"""
        
        # Trip planning: home -> transit -> work with walking segments
        self.run_query(
            """
            // Simulate a trip: residential area -> downtown via transit
            WITH point({latitude: 47.6205, longitude: -122.3493}) as home_location,  // Fremont
                 point({latitude: 47.6062, longitude: -122.3321}) as work_location   // Downtown
            
            // Find closest transit stop to home
            MATCH (home_stop:TransitStop)
            WHERE home_stop.location IS NOT NULL
            WITH home_location, work_location, home_stop,
                 point.distance(home_location, home_stop.location) as home_walk_distance
            ORDER BY home_walk_distance
            LIMIT 3
            
            // Find transit stops near work
            WITH home_location, work_location, home_stop, home_walk_distance
            MATCH (work_stop:TransitStop)
            WHERE work_stop.location IS NOT NULL 
                  AND point.distance(work_location, work_stop.location) <= 800
            WITH home_stop, work_stop, home_walk_distance,
                 point.distance(work_location, work_stop.location) as work_walk_distance
            
            // Find path between transit stops via places
            MATCH path = shortestPath((home_stop)-[:WITHIN_500M*1..10]-(work_stop))
            WHERE home_stop <> work_stop
            
            RETURN home_stop.stop_name as start_stop,
                   work_stop.stop_name as end_stop,
                   round(home_walk_distance) as walk_to_transit_m,
                   round(work_walk_distance) as walk_from_transit_m,
                   length(path) as transit_hops,
                   round(home_walk_distance + work_walk_distance) as total_walk_m
            ORDER BY total_walk_m + (transit_hops * 100)  // Prefer fewer hops
            LIMIT 10
            """,
            description="Multi-modal trip: Fremont to Downtown (walk + transit)"
        )
        
        # Commuter analysis: residential to business district connectivity
        self.run_query(
            """
            MATCH (residential:Place)-[:BELONGS_TO_CATEGORY]->(rc:Category),
                  (business:Place)-[:BELONGS_TO_CATEGORY]->(bc:Category)
            WHERE rc.label CONTAINS "Residential" AND bc.label CONTAINS "Business"
            
            MATCH path = shortestPath((residential)-[:WITHIN_500M*1..12]-(business))
            WHERE path IS NOT NULL
            
            WITH residential, business, path, length(path) as commute_complexity
            ORDER BY commute_complexity
            
            RETURN residential.name as residential_area,
                   residential.locality as from_locality,
                   business.name as business_area,
                   business.locality as to_locality,
                   commute_complexity,
                   [n in nodes(path) WHERE n:TransitStop | n.stop_name][0..3] as transit_route
            LIMIT 15
            """,
            description="Residential to business district commute routes"
        )
    
    def clustering_and_hubs(self):
        """Identify transit hubs and place clusters"""
        
        # Transit hub analysis: stops connecting most places
        self.run_query(
            """
            MATCH (ts:TransitStop)-[:WITHIN_500M]-(p:Place)
            WITH ts, collect(p) as connected_places
            WHERE size(connected_places) >= 5
            
            UNWIND connected_places as place1
            UNWIND connected_places as place2
            WITH ts, place1, place2, connected_places
            WHERE place1 <> place2
            
            MATCH (place1)-[:BELONGS_TO_CATEGORY]->(c1:Category),
                  (place2)-[:BELONGS_TO_CATEGORY]->(c2:Category)
            
            WITH ts, connected_places, 
                 collect(DISTINCT c1.label) + collect(DISTINCT c2.label) as category_diversity
            
            RETURN ts.stop_name, ts.locality,
                   size(connected_places) as connected_places_count,
                   size(category_diversity) as category_diversity_count,
                   category_diversity[0..5] as top_categories
            ORDER BY connected_places_count * category_diversity_count DESC
            LIMIT 15
            """,
            description="Transit hubs with highest place connectivity and diversity"
        )
        
        # Place clusters: groups of places connected via short paths
        self.run_query(
            """
            MATCH (p1:Place)-[:WITHIN_500M*1..2]-(p2:Place)
            WHERE p1 <> p2 AND p1.locality = p2.locality
            
            WITH p1, count(p2) as cluster_connectivity
            WHERE cluster_connectivity >= 3
            
            MATCH (p1)-[:BELONGS_TO_CATEGORY]->(c:Category)
            
            RETURN p1.name, p1.locality, c.label,
                   cluster_connectivity,
                   p1.latitude, p1.longitude
            ORDER BY cluster_connectivity DESC
            LIMIT 20
            """,
            description="Highly connected place clusters (walkable areas)"
        )
        
        # Transit-place network centrality
        self.run_query(
            """
            // Find places that serve as connectors between transit stops
            MATCH (ts1:TransitStop)-[:WITHIN_500M]-(connector:Place)-[:WITHIN_500M]-(ts2:TransitStop)
            WHERE ts1 <> ts2
            
            WITH connector, count(DISTINCT ts1) + count(DISTINCT ts2) as transit_connections
            ORDER BY transit_connections DESC
            
            MATCH (connector)-[:BELONGS_TO_CATEGORY]->(c:Category)
            
            RETURN connector.name, connector.locality, c.label,
                   transit_connections,
                   connector.latitude, connector.longitude
            LIMIT 15
            """,
            description="Places serving as connectors between transit stops"
        )
    
    def spatial_routing(self):
        """Advanced spatial routing using coordinates"""
        
        # Distance-weighted routing: prefer shorter walking distances
        self.run_query(
            """
            WITH point({latitude: 47.6588, longitude: -122.3045}) as start_point  // Green Lake
            
            MATCH (nearby_stop:TransitStop)
            WHERE nearby_stop.location IS NOT NULL
            WITH start_point, nearby_stop, 
                 point.distance(start_point, nearby_stop.location) as walk_to_stop
            WHERE walk_to_stop <= 800  // Within walking distance
            ORDER BY walk_to_stop
            LIMIT 5
            
            // Find reachable destinations
            WITH nearby_stop, walk_to_stop
            MATCH (nearby_stop)-[:WITHIN_500M*1..6]-(destination:Place)-[:BELONGS_TO_CATEGORY]->(c:Category)
            WHERE c.label CONTAINS "Restaurant" OR c.label CONTAINS "Shop"
            
            WITH destination, c, nearby_stop, walk_to_stop, 
                 point.distance(nearby_stop.location, destination.location) as walk_from_stop
            
            RETURN destination.name, destination.locality, c.label,
                   nearby_stop.stop_name,
                   round(walk_to_stop) as initial_walk_m,
                   round(walk_from_stop) as final_walk_m,
                   round(walk_to_stop + walk_from_stop) as total_walk_m
            ORDER BY total_walk_m
            LIMIT 15
            """,
            description="Distance-optimized routing from Green Lake"
        )
        
        # Corridor analysis: places along transit corridors
        self.run_query(
            """
            // Find transit corridors (stops connected via places)
            MATCH (ts1:TransitStop)-[:WITHIN_500M]-(bridge:Place)-[:WITHIN_500M]-(ts2:TransitStop)
            WHERE ts1 <> ts2 AND point.distance(ts1.location, ts2.location) <= 2000
            
            WITH ts1, ts2, bridge, point.distance(ts1.location, ts2.location) as corridor_distance
            ORDER BY corridor_distance
            
            // Find other places along this corridor
            MATCH (corridor_place:Place)
            WHERE corridor_place.location IS NOT NULL
            WITH ts1, ts2, bridge, corridor_distance,
                 corridor_place,
                             point.distance(ts1.location, corridor_place.location) +
            point.distance(corridor_place.location, ts2.location) as route_distance,
            point.distance(ts1.location, ts2.location) as direct_distance
            WHERE abs(route_distance - direct_distance) <= 200  // Places roughly on the line
            
            MATCH (corridor_place)-[:BELONGS_TO_CATEGORY]->(c:Category)
            
            RETURN ts1.stop_name + " ↔ " + ts2.stop_name as corridor,
                   corridor_place.name, c.label,
                   round(corridor_distance) as corridor_length_m,
                   corridor_place.locality
            ORDER BY corridor_distance, corridor_place.name
            LIMIT 20
            """,
            description="Places along transit corridors (linear development)"
        )
    
    def run_all_routing_queries(self):
        """Run all routing analysis queries"""
        print("FOURSQUARE ROUTING & PATHFINDING ANALYSIS")
        print("="*80)
        
        print("\n\n1. SHORTEST PATH ANALYSIS")
        self.shortest_path_analysis()
        
        print("\n\n2. ACCESSIBILITY ANALYSIS")
        self.accessibility_analysis()
        
        print("\n\n3. MULTI-MODAL ROUTING")
        self.multi_modal_routing()
        
        print("\n\n4. CLUSTERING AND HUBS")
        self.clustering_and_hubs()
        
        print("\n\n5. SPATIAL ROUTING")
        self.spatial_routing()
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()

def main():
    """Main function to run routing queries"""
    try:
        # Load configuration
        config = Neo4jConfig()
        
        # Create routing analyzer
        routing = RoutingAnalysis(config)
        
        try:
            # Run all routing queries
            routing.run_all_routing_queries()
            
        finally:
            routing.close()
            
    except Exception as e:
        logger.error(f"Error running routing analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()