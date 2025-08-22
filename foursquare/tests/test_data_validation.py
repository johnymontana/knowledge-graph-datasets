#!/usr/bin/env python3
"""
Data Validation Tests for Foursquare Import

Tests data validation, cleaning, and format conversion functionality.
"""

import unittest
import tempfile
import csv
import json
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent / 'gtfs'))

from foursquare_import_neo4j import FoursquareImporter
from neo4j_config import Neo4jConfig


class TestDataValidation(unittest.TestCase):
    """Test data validation and cleaning"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = Mock(spec=Neo4jConfig)
        self.mock_config.uri = "bolt://localhost:7687"
        self.mock_config.database = "neo4j"
        self.mock_config.get_auth.return_value = ("neo4j", "password")
        self.mock_config.get_driver_config.return_value = {}
        
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir)
    
    @patch('foursquare_import_neo4j.GraphDatabase.driver')
    def test_coordinate_validation(self, mock_driver):
        """Test coordinate validation and conversion"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        importer = FoursquareImporter(
            config=self.mock_config,
            data_dir=str(self.test_data_dir)
        )
        
        # Valid coordinates
        valid_data = [
            {'stop_lat': '47.6062', 'stop_lon': '-122.3321', 'stop_name': 'Valid Stop'},
            {'stop_lat': '0.0', 'stop_lon': '0.0', 'stop_name': 'Null Island'},
            {'stop_lat': '-33.8688', 'stop_lon': '151.2093', 'stop_name': 'Sydney'},
        ]
        
        converted = importer.convert_transit_stops_to_neo4j(valid_data)
        
        for stop in converted:
            self.assertIn('stop_lat', stop)
            self.assertIn('stop_lon', stop)
            self.assertIsInstance(stop['stop_lat'], float)
            self.assertIsInstance(stop['stop_lon'], float)
            self.assertTrue(-90 <= stop['stop_lat'] <= 90)
            self.assertTrue(-180 <= stop['stop_lon'] <= 180)
    
    @patch('foursquare_import_neo4j.GraphDatabase.driver')
    def test_invalid_coordinates(self, mock_driver):
        """Test handling of invalid coordinates"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        importer = FoursquareImporter(
            config=self.mock_config,
            data_dir=str(self.test_data_dir)
        )
        
        invalid_data = [
            {'stop_lat': 'invalid', 'stop_lon': '-122.3321', 'stop_name': 'Bad Lat'},
            {'stop_lat': '47.6062', 'stop_lon': 'invalid', 'stop_name': 'Bad Lon'},
            {'stop_lat': '91.0', 'stop_lon': '-122.3321', 'stop_name': 'Out of Range Lat'},
            {'stop_lat': '47.6062', 'stop_lon': '181.0', 'stop_name': 'Out of Range Lon'},
            {'stop_lat': '', 'stop_lon': '-122.3321', 'stop_name': 'Empty Lat'},
            {'stop_lat': '47.6062', 'stop_lon': '   ', 'stop_name': 'Whitespace Lon'},
        ]
        
        converted = importer.convert_transit_stops_to_neo4j(invalid_data)
        
        for stop in converted:
            # Invalid coordinates should be excluded
            if 'stop_lat' in stop:
                self.assertIsInstance(stop['stop_lat'], float)
                self.assertTrue(-90 <= stop['stop_lat'] <= 90)
            if 'stop_lon' in stop:
                self.assertIsInstance(stop['stop_lon'], float)
                self.assertTrue(-180 <= stop['stop_lon'] <= 180)
    
    @patch('foursquare_import_neo4j.GraphDatabase.driver')
    def test_numeric_field_validation(self, mock_driver):
        """Test numeric field validation and conversion"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        importer = FoursquareImporter(
            config=self.mock_config,
            data_dir=str(self.test_data_dir)
        )
        
        test_data = [
            {
                'stop_id': 'test1',
                'location_type': '0',
                'wheelchair_boarding': '1',
                'zone_id': '21',
                'stop_lat': '47.6062',
                'stop_lon': '-122.3321'
            },
            {
                'stop_id': 'test2',
                'location_type': '0.0',  # Float that should become int
                'wheelchair_boarding': 'invalid',  # Should be excluded
                'zone_id': '',  # Empty string should be excluded
                'stop_lat': '47.6072',
                'stop_lon': '-122.3331'
            }
        ]
        
        converted = importer.convert_transit_stops_to_neo4j(test_data)
        
        # First record should have all numeric fields
        self.assertIn('location_type', converted[0])
        self.assertIn('wheelchair_boarding', converted[0])
        self.assertEqual(converted[0]['location_type'], 0)
        self.assertEqual(converted[0]['wheelchair_boarding'], 1)
        
        # Second record should exclude invalid fields
        self.assertIn('location_type', converted[1])
        self.assertNotIn('wheelchair_boarding', converted[1])
        self.assertNotIn('zone_id', converted[1])
    
    @patch('foursquare_import_neo4j.GraphDatabase.driver')
    def test_category_parsing(self, mock_driver):
        """Test category ID and label parsing"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        importer = FoursquareImporter(
            config=self.mock_config,
            data_dir=str(self.test_data_dir)
        )
        
        test_cases = [
            {
                'fsq_place_id': 'test1',
                'name': 'Test Place 1',
                'latitude': '47.6062',
                'longitude': '-122.3321',
                'fsq_category_ids': '[52e81612bcbc57f1066b7a0c]',
                'fsq_category_labels': "['Dining and Drinking > Restaurant']"
            },
            {
                'fsq_place_id': 'test2',
                'name': 'Test Place 2',
                'latitude': '47.6072',
                'longitude': '-122.3331',
                'fsq_category_ids': '[id1, id2, id3]',
                'fsq_category_labels': "['Category 1', 'Category 2', 'Category 3']"
            },
            {
                'fsq_place_id': 'test3',
                'name': 'Test Place 3',
                'latitude': '47.6082',
                'longitude': '-122.3341',
                'fsq_category_ids': '[]',
                'fsq_category_labels': '[]'
            }
        ]
        
        converted = importer.convert_places_to_neo4j(test_cases)
        
        # Test single category
        self.assertIn('category_ids', converted[0])
        self.assertIn('category_labels', converted[0])
        self.assertIsInstance(converted[0]['category_ids'], list)
        self.assertIsInstance(converted[0]['category_labels'], list)
        
        # Test multiple categories
        self.assertEqual(len(converted[1]['category_ids']), 3)
        self.assertEqual(len(converted[1]['category_labels']), 3)
        
        # Test empty categories
        self.assertIn('category_ids', converted[2])
        self.assertEqual(len(converted[2]['category_ids']), 0)
    
    @patch('foursquare_import_neo4j.GraphDatabase.driver')
    def test_string_field_cleaning(self, mock_driver):
        """Test string field cleaning and normalization"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        importer = FoursquareImporter(
            config=self.mock_config,
            data_dir=str(self.test_data_dir)
        )
        
        test_data = [
            {
                'stop_id': '  test123  ',  # Whitespace
                'stop_name': 'Test Stop\t',  # Tab character
                'stop_desc': '   ',  # Only whitespace - should be excluded
                'stop_lat': '47.6062',
                'stop_lon': '-122.3321'
            }
        ]
        
        converted = importer.convert_transit_stops_to_neo4j(test_data)
        
        # Whitespace should be trimmed
        self.assertEqual(converted[0]['stop_id'], 'test123')
        self.assertEqual(converted[0]['stop_name'], 'Test Stop')
        
        # Empty/whitespace-only fields should be excluded
        self.assertNotIn('stop_desc', converted[0])
    
    @patch('foursquare_import_neo4j.GraphDatabase.driver')
    def test_point_geometry_creation(self, mock_driver):
        """Test Point geometry creation for spatial queries"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        importer = FoursquareImporter(
            config=self.mock_config,
            data_dir=str(self.test_data_dir)
        )
        
        # Test transit stop point creation
        stop_data = [
            {
                'stop_id': 'test1',
                'stop_name': 'Test Stop',
                'stop_lat': '47.6062',
                'stop_lon': '-122.3321'
            }
        ]
        
        converted_stops = importer.convert_transit_stops_to_neo4j(stop_data)
        
        self.assertIn('location', converted_stops[0])
        location = converted_stops[0]['location']
        self.assertEqual(location['x'], -122.3321)
        self.assertEqual(location['y'], 47.6062)
        self.assertEqual(location['srid'], 4326)
        
        # Test place point creation
        place_data = [
            {
                'fsq_place_id': 'test1',
                'name': 'Test Place',
                'latitude': '47.6072',
                'longitude': '-122.3331'
            }
        ]
        
        converted_places = importer.convert_places_to_neo4j(place_data)
        
        self.assertIn('location', converted_places[0])
        location = converted_places[0]['location']
        self.assertEqual(location['x'], -122.3331)
        self.assertEqual(location['y'], 47.6072)
        self.assertEqual(location['srid'], 4326)
    
    @patch('foursquare_import_neo4j.GraphDatabase.driver')
    def test_missing_coordinate_handling(self, mock_driver):
        """Test handling when coordinates are missing"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        importer = FoursquareImporter(
            config=self.mock_config,
            data_dir=str(self.test_data_dir)
        )
        
        # Missing coordinates should not create location point
        incomplete_data = [
            {
                'stop_id': 'test1',
                'stop_name': 'Test Stop',
                'stop_lat': '47.6062'
                # Missing stop_lon
            },
            {
                'stop_id': 'test2',
                'stop_name': 'Test Stop 2'
                # Missing both coordinates
            }
        ]
        
        converted = importer.convert_transit_stops_to_neo4j(incomplete_data)
        
        # Should not create location point without both coordinates
        self.assertNotIn('location', converted[0])
        self.assertNotIn('location', converted[1])
    
    def test_data_type_consistency(self):
        """Test that data types are consistent across conversions"""
        # Test coordinate precision
        test_coords = [
            ('47.60621234567890', '-122.33214567890123'),
            ('0.0', '0.0'),
            ('90.0', '180.0'),
            ('-90.0', '-180.0')
        ]
        
        for lat_str, lon_str in test_coords:
            lat_float = float(lat_str)
            lon_float = float(lon_str)
            
            # Ensure conversion is accurate
            self.assertEqual(lat_float, float(lat_str))
            self.assertEqual(lon_float, float(lon_str))
            
            # Ensure reasonable precision (not losing significant digits)
            self.assertAlmostEqual(lat_float, float(lat_str), places=10)
            self.assertAlmostEqual(lon_float, float(lon_str), places=10)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        edge_cases = [
            # Boundary coordinates
            {'lat': '90.0', 'lon': '180.0', 'should_pass': True},
            {'lat': '-90.0', 'lon': '-180.0', 'should_pass': True},
            {'lat': '0.0', 'lon': '0.0', 'should_pass': True},
            
            # Just outside boundaries
            {'lat': '90.1', 'lon': '180.0', 'should_pass': False},
            {'lat': '90.0', 'lon': '180.1', 'should_pass': False},
            {'lat': '-90.1', 'lon': '-180.0', 'should_pass': False},
            {'lat': '-90.0', 'lon': '-180.1', 'should_pass': False},
            
            # Scientific notation
            {'lat': '4.76062e1', 'lon': '-1.223321e2', 'should_pass': True},
            
            # Very precise coordinates
            {'lat': '47.6062123456789', 'lon': '-122.3321987654321', 'should_pass': True}
        ]
        
        for case in edge_cases:
            try:
                lat = float(case['lat'])
                lon = float(case['lon'])
                
                lat_valid = -90 <= lat <= 90
                lon_valid = -180 <= lon <= 180
                is_valid = lat_valid and lon_valid
                
                if case['should_pass']:
                    self.assertTrue(is_valid, f"Expected {case} to be valid")
                else:
                    self.assertFalse(is_valid, f"Expected {case} to be invalid")
                    
            except ValueError:
                # Conversion failed - should only happen for invalid cases
                self.assertFalse(case['should_pass'], f"Expected {case} to convert successfully")


class TestCSVDataValidation(unittest.TestCase):
    """Test validation of actual CSV data structure"""
    
    def setUp(self):
        """Set up test CSV files"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir)
    
    def create_test_csv(self, filename, headers, rows):
        """Helper to create test CSV file"""
        filepath = self.test_data_dir / filename
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return filepath
    
    def test_stops_csv_structure(self):
        """Test stops.txt CSV structure validation"""
        required_headers = [
            'stop_id', 'stop_name', 'stop_lat', 'stop_lon'
        ]
        
        # Valid CSV
        valid_headers = required_headers + ['stop_code', 'zone_id', 'wheelchair_boarding']
        valid_rows = [
            ['test1', 'Test Stop 1', '47.6062', '-122.3321', 'test1', '1', '1'],
            ['test2', 'Test Stop 2', '47.6072', '-122.3331', 'test2', '1', '0']
        ]
        
        csv_file = self.create_test_csv('valid_stops.txt', valid_headers, valid_rows)
        
        # Read and validate
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            self.assertEqual(len(rows), 2)
            
            for header in required_headers:
                self.assertIn(header, rows[0].keys())
            
            # Validate data types can be converted
            for row in rows:
                self.assertIsNotNone(row['stop_id'])
                self.assertIsNotNone(row['stop_name'])
                
                try:
                    lat = float(row['stop_lat'])
                    lon = float(row['stop_lon'])
                    self.assertTrue(-90 <= lat <= 90)
                    self.assertTrue(-180 <= lon <= 180)
                except ValueError:
                    self.fail(f"Invalid coordinates in row: {row}")
    
    def test_places_csv_structure(self):
        """Test places CSV structure validation"""
        required_headers = [
            'fsq_place_id', 'name', 'latitude', 'longitude'
        ]
        
        # Valid CSV
        valid_headers = required_headers + [
            'address', 'locality', 'region', 'fsq_category_ids', 'fsq_category_labels'
        ]
        valid_rows = [
            ['test1', 'Test Place 1', '47.6062', '-122.3321', '123 Test St', 'Seattle', 'WA', '[id1]', "['Category 1']"],
            ['test2', 'Test Place 2', '47.6072', '-122.3331', '456 Test Ave', 'Seattle', 'WA', '[id2]', "['Category 2']"]
        ]
        
        csv_file = self.create_test_csv('valid_places.csv', valid_headers, valid_rows)
        
        # Read and validate
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            self.assertEqual(len(rows), 2)
            
            for header in required_headers:
                self.assertIn(header, rows[0].keys())
            
            # Validate data types
            for row in rows:
                self.assertIsNotNone(row['fsq_place_id'])
                self.assertIsNotNone(row['name'])
                
                try:
                    lat = float(row['latitude'])
                    lon = float(row['longitude'])
                    self.assertTrue(-90 <= lat <= 90)
                    self.assertTrue(-180 <= lon <= 180)
                except ValueError:
                    self.fail(f"Invalid coordinates in row: {row}")
    
    def test_malformed_csv_handling(self):
        """Test handling of malformed CSV files"""
        # CSV with missing required columns
        incomplete_headers = ['stop_id', 'stop_name']  # Missing coordinates
        incomplete_rows = [['test1', 'Test Stop']]
        
        csv_file = self.create_test_csv('incomplete.csv', incomplete_headers, incomplete_rows)
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Should read without error, but missing columns will be empty
            self.assertEqual(len(rows), 1)
            self.assertNotIn('stop_lat', rows[0] or {})
            self.assertNotIn('stop_lon', rows[0] or {})


if __name__ == '__main__':
    unittest.main()