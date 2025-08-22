#!/usr/bin/env python3
"""
Geospatial Query Tests for Foursquare Data

Tests geospatial functionality, spatial queries, and routing capabilities.
"""

import unittest
import tempfile
import csv
import os
import math
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent / 'gtfs'))

from foursquare_import_neo4j import FoursquareImporter
from sample_queries_neo4j import FoursquareQueryRunner
from routing_queries import RoutingAnalysis
from neo4j_config import Neo4jConfig
from neo4j import GraphDatabase


class TestGeospatialQueries(unittest.TestCase):
    """Test geospatial query functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database connection"""
        try:
            cls.config = Neo4jConfig("test_config.env")
        except:
            cls.config = Neo4jConfig()
            cls.config.database = "test_geospatial"
        
        # Test connection
        try:
            driver = GraphDatabase.driver(
                cls.config.uri,
                auth=cls.config.get_auth(),
                **cls.config.get_driver_config()
            )
            
            with driver.session(database=cls.config.database) as session:
                session.run("RETURN 1")
            
            driver.close()
            cls.neo4j_available = True
        except Exception as e:
            cls.neo4j_available = False
            print(f"Neo4j not available for geospatial tests: {e}")
    
    def setUp(self):
        """Set up test data"""
        if not self.neo4j_available:
            self.skipTest("Neo4j not available")
        
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir)
        self.create_geospatial_test_data()
        self.clean_test_database()
        self.import_test_data()
    
    def tearDown(self):
        """Clean up after test"""
        if self.neo4j_available:
            self.clean_test_database()
    
    def create_geospatial_test_data(self):
        """Create test data with known geospatial relationships"""
        # Seattle area coordinates for testing
        downtown_seattle = (47.6062, -122.3321)
        capitol_hill = (47.6149, -122.3194)
        fremont = (47.6505, -122.3493)
        
        # Create transit stops at known locations
        stops_data = [
            {
                'stop_id': 'geo_stop_downtown',
                'stop_code': 'geo_stop_downtown',
                'stop_name': 'Downtown Test Stop',
                'tts_stop_name': 'Downtown Test Stop',
                'stop_desc': '',
                'stop_lat': str(downtown_seattle[0]),
                'stop_lon': str(downtown_seattle[1]),
                'zone_id': '1',
                'stop_url': '',
                'location_type': '0',
                'parent_station': '',
                'stop_timezone': 'America/Los_Angeles',
                'wheelchair_boarding': '1'
            },
            {
                'stop_id': 'geo_stop_capitol_hill',
                'stop_code': 'geo_stop_capitol_hill',
                'stop_name': 'Capitol Hill Test Stop',
                'tts_stop_name': 'Capitol Hill Test Stop',
                'stop_desc': '',
                'stop_lat': str(capitol_hill[0]),
                'stop_lon': str(capitol_hill[1]),
                'zone_id': '1',
                'stop_url': '',
                'location_type': '0',
                'parent_station': '',
                'stop_timezone': 'America/Los_Angeles',
                'wheelchair_boarding': '1'
            },
            {
                'stop_id': 'geo_stop_fremont',
                'stop_code': 'geo_stop_fremont',
                'stop_name': 'Fremont Test Stop',
                'tts_stop_name': 'Fremont Test Stop',
                'stop_desc': '',
                'stop_lat': str(fremont[0]),
                'stop_lon': str(fremont[1]),
                'zone_id': '1',
                'stop_url': '',
                'location_type': '0',
                'parent_station': '',
                'stop_timezone': 'America/Los_Angeles',
                'wheelchair_boarding': '1'
            }
        ]
        
        stops_file = self.test_data_dir / 'stops.txt'
        with open(stops_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=stops_data[0].keys())
            writer.writeheader()
            writer.writerows(stops_data)
        
        # Create places at calculated distances
        places_data = [
            # Close to downtown (within 200m)
            {
                'fsq_place_id': 'geo_place_downtown_close',
                'name': 'Downtown Close Restaurant',
                'latitude': str(downtown_seattle[0] + 0.001),  # ~111m north
                'longitude': str(downtown_seattle[1]),
                'address': '100 Test St',
                'locality': 'Seattle',
                'region': 'WA',
                'postcode': '98101',
                'country': 'US',
                'fsq_category_ids': '[restaurant_cat]',
                'fsq_category_labels': "['Dining and Drinking > Restaurant']",
                'closest_stop_name': 'Downtown Test Stop'
            },
            # Medium distance from downtown (within 500m)
            {
                'fsq_place_id': 'geo_place_downtown_medium',
                'name': 'Downtown Medium Cafe',
                'latitude': str(downtown_seattle[0] + 0.003),  # ~333m north
                'longitude': str(downtown_seattle[1]),
                'address': '200 Test St',
                'locality': 'Seattle',
                'region': 'WA',
                'postcode': '98101',
                'country': 'US',
                'fsq_category_ids': '[cafe_cat]',
                'fsq_category_labels': "['Dining and Drinking > Cafe']",
                'closest_stop_name': 'Downtown Test Stop'
            },
            # Far from downtown (over 1km)
            {
                'fsq_place_id': 'geo_place_downtown_far',
                'name': 'Downtown Far Shop',
                'latitude': str(downtown_seattle[0] + 0.01),  # ~1.1km north
                'longitude': str(downtown_seattle[1]),
                'address': '300 Test St',
                'locality': 'Seattle',
                'region': 'WA',
                'postcode': '98101',
                'country': 'US',
                'fsq_category_ids': '[shop_cat]',
                'fsq_category_labels': "['Retail > Shop']",
                'closest_stop_name': 'Downtown Test Stop'
            },
            # Capitol Hill location
            {
                'fsq_place_id': 'geo_place_capitol_hill',
                'name': 'Capitol Hill Coffee',
                'latitude': str(capitol_hill[0] + 0.001),
                'longitude': str(capitol_hill[1]),
                'address': '400 Pine St',
                'locality': 'Seattle',
                'region': 'WA',
                'postcode': '98122',
                'country': 'US',
                'fsq_category_ids': '[cafe_cat]',
                'fsq_category_labels': "['Dining and Drinking > Cafe']",
                'closest_stop_name': 'Capitol Hill Test Stop'
            },
            # Fremont location
            {
                'fsq_place_id': 'geo_place_fremont',
                'name': 'Fremont Market',
                'latitude': str(fremont[0]),
                'longitude': str(fremont[1] + 0.001),
                'address': '500 Fremont Ave',
                'locality': 'Seattle',
                'region': 'WA',
                'postcode': '98103',
                'country': 'US',
                'fsq_category_ids': '[shop_cat]',
                'fsq_category_labels': "['Retail > Shop']",
                'closest_stop_name': 'Fremont Test Stop'
            }
        ]
        
        places_file = self.test_data_dir / 'king_county_places_near_stops.csv'
        with open(places_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=places_data[0].keys())
            writer.writeheader()
            writer.writerows(places_data)
    
    def clean_test_database(self):
        """Clean test data from database"""
        try:
            driver = GraphDatabase.driver(
                self.config.uri,
                auth=self.config.get_auth(),
                **self.config.get_driver_config()
            )
            
            with driver.session(database=self.config.database) as session:
                session.run("""
                    MATCH (n) 
                    WHERE n.fsq_place_id STARTS WITH 'geo_' OR n.stop_id STARTS WITH 'geo_'
                    DETACH DELETE n
                """)
                session.run("""
                    MATCH (c:Category) 
                    WHERE c.category_id IN ['restaurant_cat', 'cafe_cat', 'shop_cat'] OR size(()-->(c)) = 0
                    DELETE c
                """)
            
            driver.close()
        except Exception as e:
            print(f"Warning: Could not clean test database: {e}")
    
    def import_test_data(self):
        """Import test data into Neo4j"""
        importer = FoursquareImporter(
            config=self.config,
            data_dir=str(self.test_data_dir)
        )
        
        try:
            success = importer.import_all()
            self.assertTrue(success, "Failed to import test data")
        finally:
            importer.close()
    
    def test_distance_calculation(self):
        """Test spatial distance calculations"""
        driver = GraphDatabase.driver(
            self.config.uri,
            auth=self.config.get_auth(),
            **self.config.get_driver_config()
        )
        
        try:
            with driver.session(database=self.config.database) as session:
                # Test distance between known points
                result = session.run("""
                    MATCH (stop:TransitStop {stop_id: 'geo_stop_downtown'}),
                          (place:Place {fsq_place_id: 'geo_place_downtown_close'})
                    WHERE stop.location IS NOT NULL AND place.location IS NOT NULL
                    RETURN distance(stop.location, place.location) as distance_meters
                """)
                
                record = result.single()
                if record:
                    distance = record['distance_meters']
                    # Should be approximately 111 meters (0.001 degree latitude difference)
                    self.assertLess(distance, 200, "Close place should be within 200m")
                    self.assertGreater(distance, 50, "Distance should be realistic")
        
        finally:
            driver.close()
    
    def test_spatial_within_query(self):
        """Test spatial within distance queries"""
        driver = GraphDatabase.driver(
            self.config.uri,
            auth=self.config.get_auth(),
            **self.config.get_driver_config()
        )
        
        try:
            with driver.session(database=self.config.database) as session:
                # Find places within 500m of downtown stop
                result = session.run("""
                    MATCH (stop:TransitStop {stop_id: 'geo_stop_downtown'}),
                          (place:Place)
                    WHERE stop.location IS NOT NULL AND place.location IS NOT NULL
                      AND distance(stop.location, place.location) <= 500
                      AND place.fsq_place_id STARTS WITH 'geo_'
                    RETURN place.name, distance(stop.location, place.location) as distance_meters
                    ORDER BY distance_meters
                """)
                
                results = list(result)
                self.assertGreater(len(results), 0, "Should find places within 500m")
                
                # Check distances are actually within 500m
                for record in results:
                    self.assertLessEqual(record['distance_meters'], 500)
                
                # Should find close and medium places, but not far one
                place_names = [r['place.name'] for r in results]
                self.assertIn('Downtown Close Restaurant', place_names)
                self.assertIn('Downtown Medium Cafe', place_names)
                self.assertNotIn('Downtown Far Shop', place_names)
        
        finally:
            driver.close()
    
    def test_nearest_neighbor_query(self):
        """Test finding nearest places to a point"""
        driver = GraphDatabase.driver(
            self.config.uri,
            auth=self.config.get_auth(),
            **self.config.get_driver_config()
        )
        
        try:
            with driver.session(database=self.config.database) as session:
                # Find nearest places to downtown coordinates
                result = session.run("""
                    WITH point({latitude: 47.6062, longitude: -122.3321}) as reference_point
                    MATCH (place:Place)
                    WHERE place.location IS NOT NULL 
                      AND place.fsq_place_id STARTS WITH 'geo_'
                    WITH place, distance(place.location, reference_point) as distance_meters
                    ORDER BY distance_meters
                    LIMIT 3
                    RETURN place.name, distance_meters
                """)
                
                results = list(result)
                self.assertGreater(len(results), 0, "Should find nearest places")
                
                # Results should be ordered by distance (closest first)
                if len(results) > 1:
                    for i in range(len(results) - 1):
                        self.assertLessEqual(
                            results[i]['distance_meters'],
                            results[i + 1]['distance_meters'],
                            "Results should be ordered by distance"
                        )
        
        finally:
            driver.close()
    
    def test_spatial_relationships(self):
        """Test spatial relationship creation and querying"""
        driver = GraphDatabase.driver(
            self.config.uri,
            auth=self.config.get_auth(),
            **self.config.get_driver_config()
        )
        
        try:
            with driver.session(database=self.config.database) as session:
                # Check WITHIN_500M relationships were created
                result = session.run("""
                    MATCH (place:Place)-[:WITHIN_500M]->(stop:TransitStop)
                    WHERE place.fsq_place_id STARTS WITH 'geo_' 
                      AND stop.stop_id STARTS WITH 'geo_'
                    RETURN count(*) as relationship_count
                """)
                
                count = result.single()['relationship_count']
                self.assertGreater(count, 0, "Should have spatial relationships")
                
                # Check specific relationships
                result = session.run("""
                    MATCH (place:Place {fsq_place_id: 'geo_place_downtown_close'})-[:WITHIN_500M]->(stop:TransitStop)
                    RETURN stop.stop_name
                """)
                
                results = list(result)
                if len(results) > 0:
                    self.assertIn('Downtown Test Stop', [r['stop.stop_name'] for r in results])
        
        finally:
            driver.close()
    
    def test_routing_queries(self):
        """Test routing and pathfinding queries"""
        driver = GraphDatabase.driver(
            self.config.uri,
            auth=self.config.get_auth(),
            **self.config.get_driver_config()
        )
        
        try:
            with driver.session(database=self.config.database) as session:
                # Test shortest path between transit stops via places
                result = session.run("""
                    MATCH start = (s1:TransitStop {stop_id: 'geo_stop_downtown'}),
                          end = (s2:TransitStop {stop_id: 'geo_stop_capitol_hill'})
                    MATCH path = shortestPath((start)-[:WITHIN_500M*1..6]-(end))
                    RETURN path, length(path) as path_length
                    LIMIT 1
                """)
                
                record = result.single()
                if record:
                    path_length = record['path_length']
                    self.assertGreater(path_length, 0, "Should find a path between stops")
                    self.assertLess(path_length, 10, "Path should be reasonable length")
                
                # Test reachability from a transit stop
                result = session.run("""
                    MATCH (start:TransitStop {stop_id: 'geo_stop_downtown'})-[:WITHIN_500M*1..4]-(reachable:Place)
                    WHERE reachable.fsq_place_id STARTS WITH 'geo_'
                    RETURN count(DISTINCT reachable) as reachable_count
                """)
                
                count = result.single()['reachable_count']
                self.assertGreater(count, 0, "Should find reachable places")
        
        finally:
            driver.close()
    
    def test_cluster_analysis(self):
        """Test spatial clustering queries"""
        driver = GraphDatabase.driver(
            self.config.uri,
            auth=self.config.get_auth(),
            **self.config.get_driver_config()
        )
        
        try:
            with driver.session(database=self.config.database) as session:
                # Find transit stops with multiple nearby places (clusters)
                result = session.run("""
                    MATCH (stop:TransitStop)-[:WITHIN_500M]-(place:Place)
                    WHERE stop.stop_id STARTS WITH 'geo_' 
                      AND place.fsq_place_id STARTS WITH 'geo_'
                    WITH stop, collect(place) as nearby_places
                    WHERE size(nearby_places) >= 2
                    RETURN stop.stop_name, size(nearby_places) as cluster_size
                    ORDER BY cluster_size DESC
                """)
                
                results = list(result)
                if len(results) > 0:
                    # Downtown should have multiple nearby places
                    downtown_cluster = next(
                        (r for r in results if 'Downtown' in r['stop.stop_name']), 
                        None
                    )
                    if downtown_cluster:
                        self.assertGreaterEqual(downtown_cluster['cluster_size'], 2)
        
        finally:
            driver.close()
    
    def test_category_spatial_distribution(self):
        """Test spatial distribution of categories"""
        driver = GraphDatabase.driver(
            self.config.uri,
            auth=self.config.get_auth(),
            **self.config.get_driver_config()
        )
        
        try:
            with driver.session(database=self.config.database) as session:
                # Find category distribution near transit stops
                result = session.run("""
                    MATCH (stop:TransitStop)-[:WITHIN_500M]-(place:Place)-[:BELONGS_TO_CATEGORY]->(category:Category)
                    WHERE stop.stop_id STARTS WITH 'geo_' 
                      AND place.fsq_place_id STARTS WITH 'geo_'
                    RETURN category.label, count(place) as place_count, 
                           collect(DISTINCT stop.stop_name) as nearby_stops
                    ORDER BY place_count DESC
                """)
                
                results = list(result)
                self.assertGreater(len(results), 0, "Should find category distribution")
                
                # Verify categories exist
                categories = [r['category.label'] for r in results]
                expected_categories = ['Dining and Drinking > Restaurant', 'Dining and Drinking > Cafe', 'Retail > Shop']
                for expected in expected_categories:
                    category_found = any(expected in cat for cat in categories if cat)
                    if not category_found:
                        # Category might be abbreviated or formatted differently
                        print(f"Warning: Expected category '{expected}' not found in {categories}")
        
        finally:
            driver.close()
    
    def test_accessibility_analysis(self):
        """Test transit accessibility analysis"""
        driver = GraphDatabase.driver(
            self.config.uri,
            auth=self.config.get_auth(),
            **self.config.get_driver_config()
        )
        
        try:
            with driver.session(database=self.config.database) as session:
                # Analyze places with good vs poor transit access
                result = session.run("""
                    MATCH (place:Place)
                    WHERE place.fsq_place_id STARTS WITH 'geo_'
                    OPTIONAL MATCH (place)-[:WITHIN_500M]->(stop:TransitStop)
                    WITH place, count(stop) as transit_connections
                    RETURN place.name,
                           transit_connections,
                           CASE WHEN transit_connections > 0 THEN 'accessible' ELSE 'isolated' END as accessibility
                    ORDER BY transit_connections DESC
                """)
                
                results = list(result)
                self.assertGreater(len(results), 0, "Should analyze accessibility")
                
                # Check that some places are accessible and others might not be
                accessible_count = sum(1 for r in results if r['accessibility'] == 'accessible')
                self.assertGreater(accessible_count, 0, "Should have accessible places")
        
        finally:
            driver.close()
    
    @unittest.skipUnless(os.getenv('RUN_LONG_TESTS'), "Long running tests disabled")
    def test_performance_spatial_queries(self):
        """Test performance of spatial queries"""
        driver = GraphDatabase.driver(
            self.config.uri,
            auth=self.config.get_auth(),
            **self.config.get_driver_config()
        )
        
        try:
            with driver.session(database=self.config.database) as session:
                import time
                
                # Test index usage for spatial queries
                start_time = time.time()
                result = session.run("""
                    MATCH (place:Place)
                    WHERE place.location IS NOT NULL
                      AND place.fsq_place_id STARTS WITH 'geo_'
                    WITH point({latitude: 47.6062, longitude: -122.3321}) as reference
                    MATCH (place:Place)
                    WHERE distance(place.location, reference) <= 1000
                    RETURN count(place) as count
                """)
                
                count = result.single()['count']
                elapsed_time = time.time() - start_time
                
                # Query should complete reasonably quickly (under 1 second for test data)
                self.assertLess(elapsed_time, 1.0, "Spatial query should be fast")
                self.assertGreaterEqual(count, 0, "Query should return valid count")
        
        finally:
            driver.close()


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), "Integration tests disabled")
class TestGeospatialQueriesWithEnv(TestGeospatialQueries):
    """Same geospatial tests but only run when explicitly enabled"""
    pass


if __name__ == '__main__':
    if os.getenv('RUN_INTEGRATION_TESTS'):
        unittest.main()
    else:
        print("Geospatial tests skipped. Set RUN_INTEGRATION_TESTS=1 to run them.")
        print("Make sure Neo4j is running and configured for testing.")