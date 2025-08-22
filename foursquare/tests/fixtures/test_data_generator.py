#!/usr/bin/env python3
"""
Test Data Generator for Foursquare Tests

Generates realistic test data for various test scenarios.
"""

import csv
import json
import random
import math
from pathlib import Path
from typing import List, Dict, Tuple, Any


class TestDataGenerator:
    """Generates test data for Foursquare import tests"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Seattle area bounds for realistic coordinates
        self.seattle_bounds = {
            'lat_min': 47.4810,
            'lat_max': 47.7341,
            'lon_min': -122.4594,
            'lon_max': -122.2244
        }
        
        # Sample categories
        self.categories = [
            {
                'id': '52e81612bcbc57f1066b7a0c',
                'label': 'Dining and Drinking > Restaurant'
            },
            {
                'id': '4bf58dd8d48988d16d941735',
                'label': 'Dining and Drinking > Cafe, Coffee, and Tea House'
            },
            {
                'id': '52f2ab2ebcbc57f1066b8b57',
                'label': 'Retail > Shop'
            },
            {
                'id': '4bf58dd8d48988d193941735',
                'label': 'Business and Professional Services > Office'
            },
            {
                'id': '4bf58dd8d48988d164941735',
                'label': 'Health and Medicine > Hospital'
            },
            {
                'id': '4e67e38e036454776db1fb3a',
                'label': 'Education > School'
            },
            {
                'id': '52e81612bcbc57f1066b7a21',
                'label': 'Retail > Grocery Store'
            },
            {
                'id': '4bf58dd8d48988d1fd941735',
                'label': 'Automotive > Gas Station'
            }
        ]
        
        # Sample neighborhoods
        self.neighborhoods = [
            'Capitol Hill', 'Fremont', 'Ballard', 'Queen Anne', 'Wallingford',
            'Greenwood', 'Phinney Ridge', 'Magnolia', 'Beacon Hill', 'Georgetown'
        ]
    
    def generate_coordinate_in_bounds(self) -> Tuple[float, float]:
        """Generate random coordinate within Seattle bounds"""
        lat = random.uniform(self.seattle_bounds['lat_min'], self.seattle_bounds['lat_max'])
        lon = random.uniform(self.seattle_bounds['lon_min'], self.seattle_bounds['lon_max'])
        return lat, lon
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in meters"""
        # Haversine formula
        R = 6371000  # Earth's radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2) ** 2 + 
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def generate_nearby_coordinate(self, lat: float, lon: float, max_distance_m: float) -> Tuple[float, float]:
        """Generate coordinate within specified distance"""
        # Convert distance to approximate degrees (rough approximation)
        lat_degrees_per_meter = 1 / 111000
        lon_degrees_per_meter = 1 / (111000 * math.cos(math.radians(lat)))
        
        max_lat_offset = max_distance_m * lat_degrees_per_meter
        max_lon_offset = max_distance_m * lon_degrees_per_meter
        
        lat_offset = random.uniform(-max_lat_offset, max_lat_offset)
        lon_offset = random.uniform(-max_lon_offset, max_lon_offset)
        
        return lat + lat_offset, lon + lon_offset
    
    def generate_transit_stops(self, count: int = 10, prefix: str = "test") -> List[Dict[str, Any]]:
        """Generate test transit stops"""
        stops = []
        
        for i in range(count):
            lat, lon = self.generate_coordinate_in_bounds()
            neighborhood = random.choice(self.neighborhoods)
            
            stop = {
                'stop_id': f'{prefix}_stop_{i+1}',
                'stop_code': f'{prefix}_stop_{i+1}',
                'stop_name': f'{neighborhood} Test Stop {i+1}',
                'tts_stop_name': f'{neighborhood} Test Stop {i+1}',
                'stop_desc': f'Test transit stop in {neighborhood}',
                'stop_lat': f'{lat:.6f}',
                'stop_lon': f'{lon:.6f}',
                'zone_id': str(random.randint(1, 3)),
                'stop_url': '',
                'location_type': '0',
                'parent_station': '',
                'stop_timezone': 'America/Los_Angeles',
                'wheelchair_boarding': str(random.randint(0, 1))
            }
            stops.append(stop)
        
        return stops
    
    def generate_places(self, stops: List[Dict[str, Any]], places_per_stop: int = 3, prefix: str = "test") -> List[Dict[str, Any]]:
        """Generate test places near transit stops"""
        places = []
        place_counter = 1
        
        for stop in stops:
            stop_lat = float(stop['stop_lat'])
            stop_lon = float(stop['stop_lon'])
            
            # Generate places at various distances
            distances = [100, 300, 600]  # meters
            
            for j in range(places_per_stop):
                # Choose distance (some close, some medium, some far)
                max_distance = distances[j % len(distances)]
                place_lat, place_lon = self.generate_nearby_coordinate(stop_lat, stop_lon, max_distance)
                
                category = random.choice(self.categories)
                business_names = [
                    'Coffee House', 'Restaurant', 'Market', 'Bookstore', 'Pharmacy',
                    'Bank', 'Clinic', 'Gym', 'Salon', 'Bakery'
                ]
                
                place_name = f"{random.choice(business_names)} #{place_counter}"
                
                place = {
                    'fsq_place_id': f'{prefix}_place_{place_counter}',
                    'name': place_name,
                    'latitude': f'{place_lat:.6f}',
                    'longitude': f'{place_lon:.6f}',
                    'address': f'{random.randint(100, 9999)} Test St',
                    'locality': 'Seattle',
                    'region': 'WA',
                    'postcode': f'981{random.randint(10, 99):02d}',
                    'admin_region': 'King County',
                    'post_town': 'Seattle',
                    'po_box': '',
                    'country': 'US',
                    'date_created': '2020-01-01',
                    'date_refreshed': '2024-01-01',
                    'date_closed': '',
                    'tel': f'(206) 555-{random.randint(1000, 9999)}' if random.random() > 0.3 else '',
                    'website': f'https://{place_name.lower().replace(" ", "").replace("#", "")}.com' if random.random() > 0.5 else '',
                    'email': '',
                    'facebook_id': '',
                    'instagram': '',
                    'twitter': '',
                    'fsq_category_ids': f'[{category["id"]}]',
                    'fsq_category_labels': f'[\'{category["label"]}\']',
                    'placemaker_url': f'https://foursquare.com/{prefix}/{place_counter}',
                    'dt': '2025-04-08',
                    'closest_stop_name': stop['stop_name']
                }
                places.append(place)
                place_counter += 1
        
        return places
    
    def generate_spatial_test_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Generate data specifically for spatial testing"""
        # Fixed locations for predictable spatial relationships
        downtown = (47.6062, -122.3321)
        capitol_hill = (47.6149, -122.3194)
        fremont = (47.6505, -122.3493)
        
        stops = [
            {
                'stop_id': 'spatial_test_downtown',
                'stop_code': 'spatial_test_downtown',
                'stop_name': 'Downtown Spatial Test Stop',
                'tts_stop_name': 'Downtown Spatial Test Stop',
                'stop_desc': 'Test stop for spatial queries',
                'stop_lat': f'{downtown[0]:.6f}',
                'stop_lon': f'{downtown[1]:.6f}',
                'zone_id': '1',
                'stop_url': '',
                'location_type': '0',
                'parent_station': '',
                'stop_timezone': 'America/Los_Angeles',
                'wheelchair_boarding': '1'
            },
            {
                'stop_id': 'spatial_test_capitol_hill',
                'stop_code': 'spatial_test_capitol_hill',
                'stop_name': 'Capitol Hill Spatial Test Stop',
                'tts_stop_name': 'Capitol Hill Spatial Test Stop',
                'stop_desc': 'Test stop for spatial queries',
                'stop_lat': f'{capitol_hill[0]:.6f}',
                'stop_lon': f'{capitol_hill[1]:.6f}',
                'zone_id': '1',
                'stop_url': '',
                'location_type': '0',
                'parent_station': '',
                'stop_timezone': 'America/Los_Angeles',
                'wheelchair_boarding': '1'
            },
            {
                'stop_id': 'spatial_test_fremont',
                'stop_code': 'spatial_test_fremont',
                'stop_name': 'Fremont Spatial Test Stop',
                'tts_stop_name': 'Fremont Spatial Test Stop',
                'stop_desc': 'Test stop for spatial queries',
                'stop_lat': f'{fremont[0]:.6f}',
                'stop_lon': f'{fremont[1]:.6f}',
                'zone_id': '1',
                'stop_url': '',
                'location_type': '0',
                'parent_station': '',
                'stop_timezone': 'America/Los_Angeles',
                'wheelchair_boarding': '1'
            }
        ]
        
        places = []
        place_id = 1
        
        # Places at known distances from downtown
        test_distances = [
            (0.001, 'very_close'),  # ~111m
            (0.003, 'close'),       # ~333m
            (0.005, 'medium'),      # ~555m
            (0.008, 'far'),         # ~888m
            (0.015, 'very_far')     # ~1.6km
        ]
        
        for offset, distance_label in test_distances:
            place = {
                'fsq_place_id': f'spatial_test_downtown_{distance_label}',
                'name': f'Downtown {distance_label.replace("_", " ").title()} Place',
                'latitude': f'{downtown[0] + offset:.6f}',
                'longitude': f'{downtown[1]:.6f}',
                'address': f'{place_id * 100} Test Street',
                'locality': 'Seattle',
                'region': 'WA',
                'postcode': '98101',
                'admin_region': 'King County',
                'post_town': 'Seattle',
                'po_box': '',
                'country': 'US',
                'date_created': '2020-01-01',
                'date_refreshed': '2024-01-01',
                'date_closed': '',
                'tel': '',
                'website': '',
                'email': '',
                'facebook_id': '',
                'instagram': '',
                'twitter': '',
                'fsq_category_ids': '[52e81612bcbc57f1066b7a0c]',
                'fsq_category_labels': "['Dining and Drinking > Restaurant']",
                'placemaker_url': f'https://foursquare.com/spatial_test/{place_id}',
                'dt': '2025-04-08',
                'closest_stop_name': 'Downtown Spatial Test Stop'
            }
            places.append(place)
            place_id += 1
        
        return stops, places
    
    def save_stops_csv(self, stops: List[Dict[str, Any]], filename: str = 'stops.txt'):
        """Save stops data to CSV file"""
        filepath = self.output_dir / filename
        
        if stops:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=stops[0].keys())
                writer.writeheader()
                writer.writerows(stops)
    
    def save_places_csv(self, places: List[Dict[str, Any]], filename: str = 'king_county_places_near_stops.csv'):
        """Save places data to CSV file"""
        filepath = self.output_dir / filename
        
        if places:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=places[0].keys())
                writer.writeheader()
                writer.writerows(places)
    
    def generate_all_test_data(self, stops_count: int = 5, places_per_stop: int = 3):
        """Generate complete test dataset"""
        print(f"Generating test data: {stops_count} stops, {places_per_stop} places per stop")
        
        # Generate standard test data
        stops = self.generate_transit_stops(stops_count)
        places = self.generate_places(stops, places_per_stop)
        
        # Save standard test data
        self.save_stops_csv(stops, 'test_stops.txt')
        self.save_places_csv(places, 'test_places.csv')
        
        # Generate spatial test data
        spatial_stops, spatial_places = self.generate_spatial_test_data()
        
        # Save spatial test data
        self.save_stops_csv(spatial_stops, 'spatial_test_stops.txt')
        self.save_places_csv(spatial_places, 'spatial_test_places.csv')
        
        # Generate minimal test data for unit tests
        minimal_stops = self.generate_transit_stops(2, prefix="unit")
        minimal_places = self.generate_places(minimal_stops, 1, prefix="unit")
        
        self.save_stops_csv(minimal_stops, 'unit_test_stops.txt')
        self.save_places_csv(minimal_places, 'unit_test_places.csv')
        
        print(f"Generated test data saved to {self.output_dir}")
        print(f"- {len(stops)} standard stops, {len(places)} standard places")
        print(f"- {len(spatial_stops)} spatial stops, {len(spatial_places)} spatial places")
        print(f"- {len(minimal_stops)} unit test stops, {len(minimal_places)} unit test places")


def main():
    """Generate test data"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test data for Foursquare tests")
    parser.add_argument("--output-dir", default="tests/fixtures/data", help="Output directory")
    parser.add_argument("--stops", type=int, default=5, help="Number of stops to generate")
    parser.add_argument("--places-per-stop", type=int, default=3, help="Places per stop")
    
    args = parser.parse_args()
    
    generator = TestDataGenerator(args.output_dir)
    generator.generate_all_test_data(args.stops, args.places_per_stop)


if __name__ == "__main__":
    main()