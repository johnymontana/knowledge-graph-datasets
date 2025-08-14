#!/usr/bin/env python3
"""
Sample Queries for GTFS Data in Dgraph

This script demonstrates various queries you can run against the imported GTFS data.
"""

import json
from typing import Dict, Any
import pydgraph
from dgraph_config import DgraphConfig

class GTFSQueryClient:
    """Client for querying GTFS data in Dgraph using pydgraph"""
    
    def __init__(self, config: DgraphConfig = None):
        if config is None:
            config = DgraphConfig()
        
        self.config = config
        # Create pydgraph client using connection string
        self.client = pydgraph.open(config.connection_string)
    
    def run_query(self, query: str) -> Dict[str, Any]:
        """Run a DQL query against Dgraph using pydgraph"""
        try:
            txn = self.client.txn()
            try:
                response = txn.query(query)
                return response
            finally:
                txn.discard()
                
        except Exception as e:
            print(f"Error running query: {e}")
            return {}
    
    def query_agencies(self) -> Dict[str, Any]:
        """Query all transit agencies"""
        query = """
        {
            agencies(func: type(Agency)) {
                agency_id
                agency_name
                agency_url
                agency_timezone
            }
        }
        """
        return self.run_query(query)
    
    def query_routes_by_type(self, route_type: int = 3) -> Dict[str, Any]:
        """Query routes by type (3 = Bus, 4 = Ferry, etc.)"""
        query = f"""
        {{
            routes(func: type(Route)) @filter(eq(route_type, {route_type})) {{
                route_id
                route_short_name
                route_long_name
                route_type
            }}
        }}
        """
        return self.run_query(query)
    
    def query_stops_in_area(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> Dict[str, Any]:
        """Query stops within a geographic bounding box"""
        query = f"""
        {{
            stops(func: type(Stop)) @filter(ge(stop_lat, {min_lat}) AND le(stop_lat, {max_lat}) AND ge(stop_lon, {min_lon}) AND le(stop_lon, {max_lon})) {{
                stop_id
                stop_name
                stop_lat
                stop_lon
                stop_code
            }}
        }}
        """
        return self.run_query(query)
    
    def query_trips_for_route(self, route_id: str) -> Dict[str, Any]:
        """Query trips for a specific route"""
        query = f"""
        {{
            trips(func: type(Trip)) @filter(eq(route_id, "{route_id}")) {{
                trip_id
                trip_headsign
                direction_id
            }}
        }}
        """
        return self.run_query(query)
    
    def query_stops_with_transfers(self) -> Dict[str, Any]:
        """Query stops that have transfer connections"""
        query = """
        {
            stops(func: type(Stop), first: 10) {
                stop_id
                stop_name
                stop_lat
                stop_lon
            }
        }
        """
        return self.run_query(query)
    
    def query_fare_information(self) -> Dict[str, Any]:
        """Query fare information"""
        query = """
        {
            fares(func: type(FareAttribute), first: 10) {
                fare_id
                price
                currency_type
                payment_method
                transfers
            }
        }
        """
        return self.run_query(query)
    
    def query_service_calendar(self, service_id: str = None) -> Dict[str, Any]:
        """Query service calendar information"""
        if service_id:
            query = f"""
            {{
                calendar(func: type(Calendar)) @filter(eq(service_id, "{service_id}")) {{
                    service_id
                    monday
                    tuesday
                    wednesday
                    thursday
                    friday
                    saturday
                    sunday
                    start_date
                    end_date
                }}
            }}
            """
        else:
            query = """
            {
                calendar(func: type(Calendar), first: 10) {
                    service_id
                    monday
                    tuesday
                    wednesday
                    thursday
                    friday
                    saturday
                    sunday
                    start_date
                    end_date
                }
            }
            """
        return self.run_query(query)
    
    def query_stops_near_point(self, lat: float, lon: float, radius_km: float = 1.0) -> Dict[str, Any]:
        """Query stops within a certain radius of a point"""
        # For now, use a simple bounding box approach since we don't have geo indexing
        radius_deg = radius_km / 111.0  # Approximate conversion
        min_lat = lat - radius_deg
        max_lat = lat + radius_deg
        min_lon = lon - radius_deg
        max_lon = lon + radius_deg
        
        return self.query_stops_in_area(min_lat, max_lat, min_lon, max_lon)
    
    def query_stops_in_polygon(self, coordinates: list) -> Dict[str, Any]:
        """Query stops within a polygon area"""
        # For now, use a simple bounding box approach
        lons = [coord[0] for coord in coordinates]
        lats = [coord[1] for coord in coordinates]
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        return self.query_stops_in_area(min_lat, max_lat, min_lon, max_lon)

def print_results(title: str, results: Dict[str, Any]):
    """Pretty print query results for pydgraph responses"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    
    if not results:
        print("No results found or query failed.")
        return
    
    # pydgraph returns results in a different format
    if hasattr(results, 'json'):
        # Convert pydgraph response to dict
        json_bytes = results.json
        if isinstance(json_bytes, bytes):
            try:
                data = json.loads(json_bytes.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                print(f"Could not decode results.json: {json_bytes}")
                return
        else:
            data = json_bytes
    elif hasattr(results, 'data'):
        # Handle pydgraph response object
        data = results.data
    elif isinstance(results, bytes):
        # Handle bytes response
        try:
            data = json.loads(results.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            print(f"Could not decode response: {results}")
            return
    else:
        data = results
    
    if not data:
        print("No data returned.")
        return
    
    # Print the first few results
    for key, items in data.items():
        if isinstance(items, list):
            print(f"\n{key.upper()} ({len(items)} items):")
            for i, item in enumerate(items[:3]):  # Show first 3 items
                print(f"  {i+1}. {json.dumps(item, indent=2)}")
            if len(items) > 3:
                print(f"  ... and {len(items) - 3} more items")
        else:
            print(f"\n{key}: {json.dumps(items, indent=2)}")

def main():
    """Main function to demonstrate queries"""
    print("🚌 GTFS Data Query Examples")
    print("="*40)
    
    try:
        # Load configuration
        config = DgraphConfig()
        config.print_config()
        
        if not config.validate_connection():
            print("❌ Invalid Dgraph configuration")
            return
        
        # Initialize client
        client = GTFSQueryClient(config)
        
        # Test connection by running a simple query
        print("\nTesting connection to Dgraph...")
        try:
            # Test with a simple query
            test_response = client.run_query("schema {}")
            print("✅ Connected to Dgraph successfully!")
        except Exception as e:
            print(f"❌ Error connecting to Dgraph: {e}")
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
        
        print(f"\n{'='*60}")
        print("Query Examples Completed!")
        print(f"{'='*60}")
        print("\n💡 Tips:")
        print("• Use the Ratel UI at http://localhost:8001 for interactive queries")
        print("• Modify these queries to explore your specific data")
        print("• Check the Dgraph documentation for more query options")
        
    except Exception as e:
        print(f"❌ Error during query execution: {e}")
        return

if __name__ == "__main__":
    main()
