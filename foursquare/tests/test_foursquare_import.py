#!/usr/bin/env python3
"""
Unit Tests for Foursquare Import Module

Tests the FoursquareImporter class methods without requiring a live Neo4j connection.
"""

import unittest
import tempfile
import csv
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent / 'gtfs'))

from foursquare_import_neo4j import FoursquareImporter
from neo4j_config import Neo4jConfig


class TestFoursquareImporter(unittest.TestCase):
    """Test cases for FoursquareImporter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir)
        
        # Mock Neo4j config
        self.mock_config = Mock(spec=Neo4jConfig)
        self.mock_config.uri = "bolt://localhost:7687"
        self.mock_config.database = "neo4j"
        self.mock_config.get_auth.return_value = ("neo4j", "password")
        self.mock_config.get_driver_config.return_value = {}
        
        # Create test data files
        self.create_test_data_files()
    
    def create_test_data_files(self):
        """Create test CSV files"""
        # Create test stops.txt
        stops_data = [
            {
                'stop_id': '100',
                'stop_code': '100',
                'stop_name': '1st Ave & Spring St',
                'tts_stop_name': 'First Avenue and Spring Street',
                'stop_desc': '',
                'stop_lat': '47.6051369',
                'stop_lon': '-122.336533',
                'zone_id': '21',
                'stop_url': '',
                'location_type': '0',
                'parent_station': '',
                'stop_timezone': 'America/Los_Angeles',
                'wheelchair_boarding': '1'
            },
            {
                'stop_id': '200',
                'stop_code': '200',
                'stop_name': '2nd Ave & Spring St',
                'tts_stop_name': 'Second Avenue and Spring Street',
                'stop_desc': '',
                'stop_lat': '47.6061369',
                'stop_lon': '-122.336533',
                'zone_id': '21',
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
        
        # Create test places CSV
        places_data = [
            {
                'fsq_place_id': 'test123',
                'name': 'Test Restaurant',
                'latitude': '47.6062',
                'longitude': '-122.3321',
                'address': '123 Test St',
                'locality': 'Seattle',
                'region': 'WA',
                'postcode': '98101',
                'admin_region': '',
                'post_town': '',
                'po_box': '',
                'country': 'US',
                'date_created': '2020-01-01',
                'date_refreshed': '2020-01-01',
                'date_closed': '',
                'tel': '(206) 555-0123',
                'website': 'https://testrestaurant.com',
                'email': '',
                'facebook_id': '',
                'instagram': '',
                'twitter': '',
                'fsq_category_ids': '[52e81612bcbc57f1066b7a0c]',
                'fsq_category_labels': "['Dining and Drinking > Restaurant']",
                'placemaker_url': 'https://foursquare.com/test',
                'dt': '2025-04-08',
                'closest_stop_name': '1st Ave & Spring St'
            },
            {
                'fsq_place_id': 'test456',
                'name': 'Test Shop',
                'latitude': '47.6072',
                'longitude': '-122.3331',
                'address': '456 Test Ave',
                'locality': 'Seattle',
                'region': 'WA',
                'postcode': '98101',
                'admin_region': '',
                'post_town': '',
                'po_box': '',
                'country': 'US',
                'date_created': '2020-01-01',
                'date_refreshed': '2020-01-01',
                'date_closed': '',
                'tel': '',
                'website': '',
                'email': '',
                'facebook_id': '',
                'instagram': '',
                'twitter': '',
                'fsq_category_ids': '[52f2ab2ebcbc57f1066b8b57]',
                'fsq_category_labels': "['Retail > Shop']",
                'placemaker_url': 'https://foursquare.com/test2',
                'dt': '2025-04-08',
                'closest_stop_name': '2nd Ave & Spring St'
            }
        ]
        
        places_file = self.test_data_dir / 'king_county_places_near_stops.csv'
        with open(places_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=places_data[0].keys())
            writer.writeheader()
            writer.writerows(places_data)
    
    @patch('foursquare_import_neo4j.GraphDatabase.driver')
    def test_init(self, mock_driver):
        """Test FoursquareImporter initialization"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        importer = FoursquareImporter(
            config=self.mock_config,
            data_dir=str(self.test_data_dir),
            batch_size=100
        )
        
        self.assertEqual(importer.config, self.mock_config)
        self.assertEqual(importer.data_dir, self.test_data_dir)
        self.assertEqual(importer.batch_size, 100)
        self.assertEqual(importer.imported_count['transit_stops'], 0)
        self.assertEqual(importer.imported_count['places'], 0)
    
    @patch('foursquare_import_neo4j.GraphDatabase.driver')
    def test_read_csv_file(self, mock_driver):
        """Test CSV file reading functionality"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        importer = FoursquareImporter(
            config=self.mock_config,
            data_dir=str(self.test_data_dir)
        )
        
        # Test reading stops.txt
        stops_data = importer.read_csv_file("stops.txt")
        self.assertEqual(len(stops_data), 2)
        self.assertEqual(stops_data[0]['stop_name'], '1st Ave & Spring St')
        self.assertEqual(stops_data[1]['stop_name'], '2nd Ave & Spring St')
        
        # Test reading places CSV
        places_data = importer.read_csv_file("king_county_places_near_stops.csv")
        self.assertEqual(len(places_data), 2)
        self.assertEqual(places_data[0]['name'], 'Test Restaurant')
        self.assertEqual(places_data[1]['name'], 'Test Shop')
        
        # Test non-existent file
        empty_data = importer.read_csv_file("nonexistent.csv")
        self.assertEqual(len(empty_data), 0)
    
    @patch('foursquare_import_neo4j.GraphDatabase.driver')
    def test_convert_transit_stops_to_neo4j(self, mock_driver):
        """Test transit stops data conversion"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        importer = FoursquareImporter(
            config=self.mock_config,
            data_dir=str(self.test_data_dir)
        )
        
        raw_data = [
            {
                'stop_id': '100',
                'stop_name': 'Test Stop',
                'stop_lat': '47.6051369',
                'stop_lon': '-122.336533',
                'location_type': '0',
                'wheelchair_boarding': '1',
                'zone_id': '21'
            }
        ]
        
        converted_data = importer.convert_transit_stops_to_neo4j(raw_data)
        
        self.assertEqual(len(converted_data), 1)
        stop = converted_data[0]
        
        # Check data type conversions
        self.assertIsInstance(stop['stop_lat'], float)
        self.assertIsInstance(stop['stop_lon'], float)
        self.assertIsInstance(stop['location_type'], int)
        self.assertIsInstance(stop['wheelchair_boarding'], int)
        self.assertEqual(stop['stop_id'], '100')
        self.assertEqual(stop['stop_name'], 'Test Stop')
        
        # Check location point creation
        self.assertIn('location', stop)
        self.assertEqual(stop['location']['x'], stop['stop_lon'])
        self.assertEqual(stop['location']['y'], stop['stop_lat'])
        self.assertEqual(stop['location']['srid'], 4326)
    
    @patch('foursquare_import_neo4j.GraphDatabase.driver')
    def test_convert_places_to_neo4j(self, mock_driver):
        """Test places data conversion"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        importer = FoursquareImporter(
            config=self.mock_config,
            data_dir=str(self.test_data_dir)
        )
        
        raw_data = [
            {
                'fsq_place_id': 'test123',
                'name': 'Test Place',
                'latitude': '47.6062',
                'longitude': '-122.3321',
                'address': '123 Test St',
                'locality': 'Seattle',
                'fsq_category_ids': '[id1, id2]',
                'fsq_category_labels': "['Category 1', 'Category 2']"
            }
        ]
        
        converted_data = importer.convert_places_to_neo4j(raw_data)
        
        self.assertEqual(len(converted_data), 1)
        place = converted_data[0]
        
        # Check data type conversions
        self.assertIsInstance(place['latitude'], float)
        self.assertIsInstance(place['longitude'], float)
        self.assertEqual(place['fsq_place_id'], 'test123')
        self.assertEqual(place['name'], 'Test Place')
        
        # Check category parsing
        self.assertIn('category_ids', place)
        self.assertIn('category_labels', place)
        
        # Check location point creation
        self.assertIn('location', place)
        self.assertEqual(place['location']['x'], place['longitude'])
        self.assertEqual(place['location']['y'], place['latitude'])
        self.assertEqual(place['location']['srid'], 4326)
    
    @patch('foursquare_import_neo4j.GraphDatabase.driver')
    def test_batch_mutate(self, mock_driver):
        """Test batch mutation functionality"""
        mock_driver_instance = Mock()
        mock_session = Mock()
        mock_driver.return_value = mock_driver_instance
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        
        importer = FoursquareImporter(
            config=self.mock_config,
            data_dir=str(self.test_data_dir),
            batch_size=2
        )
        
        test_data = [
            {'id': 1, 'name': 'Test 1'},
            {'id': 2, 'name': 'Test 2'},
            {'id': 3, 'name': 'Test 3'}
        ]
        
        test_query = "CREATE (n:Test) SET n = $batch"
        
        # Mock successful execution
        mock_session.execute_write.return_value = None
        
        result = importer.batch_mutate(test_data, test_query, "test_entities")
        
        self.assertTrue(result)
        # Should be called twice (2 batches for 3 items with batch_size=2)
        self.assertEqual(mock_session.execute_write.call_count, 2)
    
    @patch('foursquare_import_neo4j.GraphDatabase.driver')
    def test_data_validation(self, mock_driver):
        """Test data validation and error handling"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        importer = FoursquareImporter(
            config=self.mock_config,
            data_dir=str(self.test_data_dir)
        )
        
        # Test invalid coordinate handling
        invalid_data = [
            {
                'stop_lat': 'invalid',
                'stop_lon': '-122.336533',
                'stop_name': 'Test Stop'
            }
        ]
        
        converted = importer.convert_transit_stops_to_neo4j(invalid_data)
        self.assertEqual(len(converted), 1)
        # Invalid lat should be skipped
        self.assertNotIn('stop_lat', converted[0])
        self.assertIn('stop_lon', converted[0])
        
        # Test empty value handling
        empty_data = [
            {
                'stop_lat': '',
                'stop_lon': '   ',
                'stop_name': 'Test Stop'
            }
        ]
        
        converted = importer.convert_transit_stops_to_neo4j(empty_data)
        self.assertEqual(len(converted), 1)
        # Empty values should be skipped
        self.assertNotIn('stop_lat', converted[0])
        self.assertNotIn('stop_lon', converted[0])
        self.assertIn('stop_name', converted[0])


class TestDataValidation(unittest.TestCase):
    """Test data validation functions"""
    
    def test_coordinate_validation(self):
        """Test coordinate validation"""
        # Valid coordinates
        valid_coords = [
            ('47.6062', '-122.3321'),  # Seattle
            ('40.7589', '-73.9851'),   # NYC
            ('-33.8688', '151.2093')   # Sydney
        ]
        
        for lat_str, lon_str in valid_coords:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                self.assertTrue(-90 <= lat <= 90)
                self.assertTrue(-180 <= lon <= 180)
            except ValueError:
                self.fail(f"Valid coordinates failed: {lat_str}, {lon_str}")
    
    def test_category_parsing(self):
        """Test category ID and label parsing"""
        # Test various category formats
        test_cases = [
            ('[id1, id2]', "['Label 1', 'Label 2']"),
            ('[single_id]', "['Single Label']"),
            ('[]', '[]')
        ]
        
        for category_ids, category_labels in test_cases:
            # Test that parsing doesn't crash
            try:
                # Remove brackets and split
                ids = category_ids.strip('[]').split(',')
                cleaned_ids = [cid.strip() for cid in ids if cid.strip()]
                
                # This should not raise an exception
                self.assertIsInstance(cleaned_ids, list)
            except Exception as e:
                self.fail(f"Category parsing failed: {e}")


if __name__ == '__main__':
    unittest.main()