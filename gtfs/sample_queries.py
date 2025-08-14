#!/usr/bin/env python3
"""
Sample Queries for GTFS Data in Dgraph

This script demonstrates various queries you can run against the imported GTFS data.
"""

import requests
import json
from typing import Dict, Any
from dgraph_config import DgraphConfig

class GTFSQueryClient:
    """Client for querying GTFS data in Dgraph"""
    
    def __init__(self, config: DgraphConfig = None):
        if config is None:
            config = DgraphConfig()
        
        self.config = config
        self.dgraph_url = config.get_http_url()
        self.query_url = f"{self.dgraph_url}/query"
        self.session = requests.Session()
        
        # Configure session with SSL and authentication
        if config.use_ssl:
            ssl_config = config.get_ssl_config()
            if ssl_config:
                self.session.verify = ssl_config.get('verify', True)
        
        # Set default headers
        self.session.headers.update(config.get_headers())
    
    def run_query(self, query: str) -> Dict[str, Any]:
        """Run a DQL query against Dgraph"""
        try:
            response = self.session.post(
                self.query_url,
                data=query,
                headers={'Content-Type': 'application/dql'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Query failed: {response.status_code}")
                print(f"Response: {response.text}")
                return {}
                
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
                routes {
                    route_short_name
                    route_long_name
                    route_type
                }
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
                agency {{
                    agency_name
                }}
            }}
        }}
        """
        return self.run_query(query)
    
    def query_stops_in_area(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> Dict[str, Any]:
        """Query stops within a geographic bounding box"""
        query = f"""
        {{
            stops(func: type(Stop)) @filter(within(location, [[{min_lon}, {min_lat}], [{max_lon}, {max_lat}]])) {{
                stop_id
                stop_name
                location
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
                route {{
                    route_short_name
                    route_long_name
                }}
                stop_times {{
                    stop_sequence
                    arrival_time
                    departure_time
                    stop {{
                        stop_name
                        stop_lat
                        stop_lon
                    }}
                }}
            }}
        }}
        """
        return self.run_query(query)
    
    def query_stops_with_transfers(self) -> Dict[str, Any]:
        """Query stops that have transfer connections"""
        query = """
        {
            stops(func: type(Stop)) @filter(has(transfers_from) OR has(transfers_to)) {
                stop_id
                stop_name
                stop_lat
                stop_lon
                transfers_from {
                    to_stop {
                        stop_name
                    }
                    min_transfer_time
                }
                transfers_to {
                    from_stop {
                        stop_name
                    }
                    min_transfer_time
                }
            }
        }
        """
        return self.run_query(query)
    
    def query_fare_information(self) -> Dict[str, Any]:
        """Query fare information"""
        query = """
        {
            fares(func: type(FareAttribute)) {
                fare_id
                price
                currency_type
                payment_method
                transfers
                fare_rules {
                    route_id
                    origin_id
                    destination_id
                }
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
                    trips {{
                        trip_id
                        route {{
                            route_short_name
                        }}
                    }}
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
        """Query stops within a certain radius of a point using geo functions"""
        query = f"""
        {{
            stops(func: type(Stop)) @filter(near(location, [{lon}, {lat}], {radius_km * 1000})) {{
                stop_id
                stop_name
                location
                stop_code
                stop_desc
            }}
        }}
        """
        return self.run_query(query)
    
    def query_stops_in_polygon(self, coordinates: list) -> Dict[str, Any]:
        """Query stops within a polygon area"""
        # coordinates should be a list of [lon, lat] pairs
        coord_str = str(coordinates)
        query = f"""
        {{
            stops(func: type(Stop)) @filter(within(location, {coord_str})) {{
                stop_id
                stop_name
                location
                stop_code
            }}
        }}
        """
        return self.run_query(query)

def print_results(title: str, results: Dict[str, Any]):
    """Pretty print query results"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    
    if not results or 'data' not in results:
        print("No results found or query failed.")
        return
    
    data = results['data']
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
        
        # Test connection
        print("\nTesting connection to Dgraph...")
        try:
            response = client.session.get(f"{client.dgraph_url}/health")
            if response.status_code == 200:
                print("✅ Connected to Dgraph successfully!")
            else:
                print(f"❌ Failed to connect to Dgraph: {response.status_code}")
                return
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

if __name__ == "__main__":
    main()
