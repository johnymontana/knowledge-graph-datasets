#!/usr/bin/env python3
"""
Sample Queries for GTFS Data in Neo4j

This script demonstrates various Cypher queries you can run against the imported GTFS data.
"""

import json
from typing import Dict, Any, List
from neo4j import GraphDatabase
from neo4j_config import Neo4jConfig

class GTFSQueryClient:
    """Client for querying GTFS data in Neo4j using Cypher"""
    
    def __init__(self, config: Neo4jConfig = None):
        if config is None:
            config = Neo4jConfig()
        
        self.config = config
        # Create Neo4j driver
        self.driver = GraphDatabase.driver(
            config.uri,
            auth=config.get_auth(),
            **config.get_driver_config()
        )
    
    def run_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Run a Cypher query against Neo4j"""
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            print(f"Error running query: {e}")
            return []
    
    def query_agencies(self) -> List[Dict[str, Any]]:
        """Query all transit agencies"""
        query = """
        MATCH (a:Agency)
        RETURN a.agency_id, a.agency_name, a.agency_url, a.agency_timezone
        ORDER BY a.agency_name
        """
        return self.run_query(query)
    
    def query_routes_by_type(self, route_type: int = 3) -> List[Dict[str, Any]]:
        """Query routes by type (3 = Bus, 4 = Ferry, etc.)"""
        query = """
        MATCH (r:Route)
        WHERE r.route_type = $route_type
        RETURN r.route_id, r.route_short_name, r.route_long_name, r.route_type
        ORDER BY r.route_short_name
        """
        return self.run_query(query, {"route_type": route_type})
    
    def query_stops_in_area(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> List[Dict[str, Any]]:
        """Query stops within a geographic bounding box"""
        query = """
        MATCH (s:Stop)
        WHERE s.stop_lat >= $min_lat AND s.stop_lat <= $max_lat 
          AND s.stop_lon >= $min_lon AND s.stop_lon <= $max_lon
        RETURN s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.stop_code
        ORDER BY s.stop_name
        """
        return self.run_query(query, {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon
        })
    
    def query_trips_for_route(self, route_id: str) -> List[Dict[str, Any]]:
        """Query trips for a specific route"""
        query = """
        MATCH (t:Trip)
        WHERE t.route_id = $route_id
        RETURN t.trip_id, t.trip_headsign, t.direction_id
        ORDER BY t.trip_headsign, t.direction_id
        """
        return self.run_query(query, {"route_id": route_id})
    
    def query_stops_with_transfers(self) -> List[Dict[str, Any]]:
        """Query stops that have transfer connections"""
        query = """
        MATCH (s:Stop)
        WHERE EXISTS {
            MATCH (t:Transfer)
            WHERE t.from_stop_id = s.stop_id OR t.to_stop_id = s.stop_id
        }
        RETURN s.stop_id, s.stop_name, s.stop_lat, s.stop_lon
        ORDER BY s.stop_name
        LIMIT 10
        """
        return self.run_query(query)
    
    def query_fare_information(self) -> List[Dict[str, Any]]:
        """Query fare information"""
        query = """
        MATCH (f:FareAttribute)
        RETURN f.fare_id, f.price, f.currency_type, f.payment_method, f.transfers
        ORDER BY f.price
        LIMIT 10
        """
        return self.run_query(query)
    
    def query_service_calendar(self, service_id: str = None) -> List[Dict[str, Any]]:
        """Query service calendar information"""
        if service_id:
            query = """
            MATCH (c:Calendar)
            WHERE c.service_id = $service_id
            RETURN c.service_id, c.monday, c.tuesday, c.wednesday, c.thursday, 
                   c.friday, c.saturday, c.sunday, c.start_date, c.end_date
            """
            return self.run_query(query, {"service_id": service_id})
        else:
            query = """
            MATCH (c:Calendar)
            RETURN c.service_id, c.monday, c.tuesday, c.wednesday, c.thursday,
                   c.friday, c.saturday, c.sunday, c.start_date, c.end_date
            ORDER BY c.service_id
            LIMIT 10
            """
            return self.run_query(query)
    
    def query_stops_near_point(self, lat: float, lon: float, radius_km: float = 1.0) -> List[Dict[str, Any]]:
        """Query stops within a certain radius of a point"""
        # For now, use a simple bounding box approach since we don't have spatial indexing
        radius_deg = radius_km / 111.0  # Approximate conversion
        min_lat = lat - radius_deg
        max_lat = lat + radius_deg
        min_lon = lon - radius_deg
        max_lon = lon + radius_deg
        
        return self.query_stops_in_area(min_lat, max_lat, min_lon, max_lon)
    
    def query_stops_in_polygon(self, coordinates: list) -> List[Dict[str, Any]]:
        """Query stops within a polygon area"""
        # For now, use a simple bounding box approach
        lons = [coord[0] for coord in coordinates]
        lats = [coord[1] for coord in coordinates]
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        return self.query_stops_in_area(min_lat, max_lat, min_lon, max_lon)
    
    def query_route_with_stops(self, route_id: str) -> List[Dict[str, Any]]:
        """Query a route with all its stops"""
        query = """
        MATCH (r:Route)-[:HAS_TRIP]->(t:Trip)-[:HAS_STOP_TIME]->(st:StopTime)-[:AT_STOP]->(s:Stop)
        WHERE r.route_id = $route_id
        RETURN DISTINCT r.route_short_name, r.route_long_name, 
               s.stop_id, s.stop_name, s.stop_lat, s.stop_lon,
               st.stop_sequence
        ORDER BY st.stop_sequence
        """
        return self.run_query(query, {"route_id": route_id})
    
    def query_trip_stops_with_times(self, trip_id: str) -> List[Dict[str, Any]]:
        """Query all stops for a trip with arrival/departure times"""
        query = """
        MATCH (t:Trip)-[:HAS_STOP_TIME]->(st:StopTime)-[:AT_STOP]->(s:Stop)
        WHERE t.trip_id = $trip_id
        RETURN s.stop_id, s.stop_name, st.arrival_time, st.departure_time, 
               st.stop_sequence, st.pickup_type, st.drop_off_type
        ORDER BY st.stop_sequence
        """
        return self.run_query(query, {"trip_id": trip_id})
    
    def query_agency_routes_stats(self) -> List[Dict[str, Any]]:
        """Query statistics about routes per agency"""
        query = """
        MATCH (a:Agency)-[:OPERATES]->(r:Route)
        RETURN a.agency_name, count(r) as route_count,
               collect(DISTINCT r.route_type) as route_types
        ORDER BY route_count DESC
        """
        return self.run_query(query)
    
    def close(self):
        """Close Neo4j driver"""
        if self.driver:
            self.driver.close()

def print_results(title: str, results: List[Dict[str, Any]]):
    """Pretty print query results"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    
    if not results:
        print("No results found or query failed.")
        return
    
    # Print the first few results
    for i, result in enumerate(results[:3]):  # Show first 3 results
        print(f"  {i+1}. {json.dumps(result, indent=2, default=str)}")
    
    if len(results) > 3:
        print(f"  ... and {len(results) - 3} more results")
    
    print(f"\nTotal results: {len(results)}")

def main():
    """Main function to demonstrate queries"""
    print("🚌 GTFS Data Query Examples (Neo4j)")
    print("="*40)
    
    client = None
    try:
        # Load configuration
        config = Neo4jConfig()
        config.print_config()
        
        if not config.validate_connection():
            print("❌ Invalid Neo4j configuration")
            return
        
        # Initialize client
        client = GTFSQueryClient(config)
        
        # Test connection by running a simple query
        print("\nTesting connection to Neo4j...")
        try:
            test_results = client.run_query("RETURN 1 as test")
            if test_results and test_results[0].get('test') == 1:
                print("✅ Connected to Neo4j successfully!")
            else:
                print("❌ Connection test failed")
                return
        except Exception as e:
            print(f"❌ Error connecting to Neo4j: {e}")
            return
        
        print("\nRunning sample queries...")
        
        # Query 1: All agencies
        results = client.query_agencies()
        print_results("All Transit Agencies", results)
        
        # Query 2: Bus routes
        results = client.query_routes_by_type(3)  # 3 = Bus
        print_results("Bus Routes", results)
        
        # Query 3: Stops in downtown Seattle area
        results = client.query_stops_in_area(47.6, 47.62, -122.35, -122.33)
        print_results("Stops in Downtown Seattle Area", results)
        
        # Query 3b: Stops near a specific point (Pike Place Market)
        results = client.query_stops_near_point(47.6097, -122.3421, 0.5)  # 0.5 km radius
        print_results("Stops Near Pike Place Market (0.5km radius)", results)
        
        # Query 4: Service calendar
        results = client.query_service_calendar()
        print_results("Service Calendar (First 10)", results)
        
        # Query 5: Fare information
        results = client.query_fare_information()
        print_results("Fare Information", results)
        
        # Query 6: Stops with transfers
        results = client.query_stops_with_transfers()
        print_results("Stops with Transfer Connections", results)
        
        # Query 7: Agency route statistics
        results = client.query_agency_routes_stats()
        print_results("Agency Route Statistics", results)
        
        print(f"\n{'='*60}")
        print("Query Examples Completed!")
        print(f"{'='*60}")
        print("\n💡 Tips:")
        print("• Use the Neo4j Browser at http://localhost:7474 for interactive queries")
        print("• Modify these queries to explore your specific data")
        print("• Check the Neo4j Cypher documentation for more query options")
        print("• Use PROFILE or EXPLAIN to optimize query performance")
        
    except Exception as e:
        print(f"❌ Error during query execution: {e}")
        
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    main()