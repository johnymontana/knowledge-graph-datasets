#!/usr/bin/env python3
"""
pytest configuration and fixtures for Foursquare tests
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent / 'gtfs'))

from foursquare_import_neo4j import FoursquareImporter
from neo4j_config import Neo4jConfig
from neo4j import GraphDatabase


@pytest.fixture(scope="session")
def test_config():
    """Create test Neo4j configuration"""
    try:
        # Try to load test-specific config
        config = Neo4jConfig("test_config.env")
    except:
        # Fall back to default config with test database
        config = Neo4jConfig()
        config.database = "test_foursquare"
    
    return config


@pytest.fixture(scope="session")
def neo4j_available(test_config):
    """Check if Neo4j is available for testing"""
    try:
        driver = GraphDatabase.driver(
            test_config.uri,
            auth=test_config.get_auth(),
            **test_config.get_driver_config()
        )
        
        with driver.session(database=test_config.database) as session:
            session.run("RETURN 1")
        
        driver.close()
        return True
    except Exception as e:
        pytest.skip(f"Neo4j not available for testing: {e}")
        return False


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_neo4j_config():
    """Mock Neo4j configuration for unit tests"""
    mock_config = Mock(spec=Neo4jConfig)
    mock_config.uri = "bolt://localhost:7687"
    mock_config.database = "test"
    mock_config.get_auth.return_value = ("neo4j", "password")
    mock_config.get_driver_config.return_value = {}
    return mock_config


@pytest.fixture
def sample_stops_data():
    """Sample transit stops data for testing"""
    return [
        {
            'stop_id': 'test_stop_1',
            'stop_code': 'test_stop_1',
            'stop_name': 'Test Stop 1',
            'tts_stop_name': 'Test Stop 1',
            'stop_desc': 'A test stop',
            'stop_lat': '47.6062',
            'stop_lon': '-122.3321',
            'zone_id': '1',
            'stop_url': '',
            'location_type': '0',
            'parent_station': '',
            'stop_timezone': 'America/Los_Angeles',
            'wheelchair_boarding': '1'
        },
        {
            'stop_id': 'test_stop_2',
            'stop_code': 'test_stop_2',
            'stop_name': 'Test Stop 2',
            'tts_stop_name': 'Test Stop 2',
            'stop_desc': 'Another test stop',
            'stop_lat': '47.6072',
            'stop_lon': '-122.3331',
            'zone_id': '1',
            'stop_url': '',
            'location_type': '0',
            'parent_station': '',
            'stop_timezone': 'America/Los_Angeles',
            'wheelchair_boarding': '0'
        }
    ]


@pytest.fixture
def sample_places_data():
    """Sample places data for testing"""
    return [
        {
            'fsq_place_id': 'test_place_1',
            'name': 'Test Coffee Shop',
            'latitude': '47.6065',
            'longitude': '-122.3325',
            'address': '123 Test Street',
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
            'tel': '(206) 555-0123',
            'website': 'https://testcoffee.com',
            'email': 'info@testcoffee.com',
            'facebook_id': '',
            'instagram': '',
            'twitter': '',
            'fsq_category_ids': '[52e81612bcbc57f1066b7a0c]',
            'fsq_category_labels': "['Dining and Drinking > Cafe, Coffee, and Tea House']",
            'placemaker_url': 'https://foursquare.com/test1',
            'dt': '2025-04-08',
            'closest_stop_name': 'Test Stop 1'
        },
        {
            'fsq_place_id': 'test_place_2',
            'name': 'Test Restaurant',
            'latitude': '47.6075',
            'longitude': '-122.3335',
            'address': '456 Test Avenue',
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
            'tel': '(206) 555-0456',
            'website': '',
            'email': '',
            'facebook_id': '',
            'instagram': '',
            'twitter': '',
            'fsq_category_ids': '[4bf58dd8d48988d1c4941735]',
            'fsq_category_labels': "['Dining and Drinking > Restaurant']",
            'placemaker_url': 'https://foursquare.com/test2',
            'dt': '2025-04-08',
            'closest_stop_name': 'Test Stop 2'
        }
    ]


@pytest.fixture
def test_csv_files(temp_data_dir, sample_stops_data, sample_places_data):
    """Create test CSV files"""
    import csv
    
    # Create stops.txt
    stops_file = temp_data_dir / 'stops.txt'
    with open(stops_file, 'w', newline='', encoding='utf-8') as f:
        if sample_stops_data:
            writer = csv.DictWriter(f, fieldnames=sample_stops_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_stops_data)
    
    # Create places CSV
    places_file = temp_data_dir / 'king_county_places_near_stops.csv'
    with open(places_file, 'w', newline='', encoding='utf-8') as f:
        if sample_places_data:
            writer = csv.DictWriter(f, fieldnames=sample_places_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_places_data)
    
    return {
        'data_dir': temp_data_dir,
        'stops_file': stops_file,
        'places_file': places_file
    }


@pytest.fixture
def clean_test_database(test_config, neo4j_available):
    """Clean test database before and after tests"""
    if not neo4j_available:
        yield
        return
    
    def cleanup():
        try:
            driver = GraphDatabase.driver(
                test_config.uri,
                auth=test_config.get_auth(),
                **test_config.get_driver_config()
            )
            
            with driver.session(database=test_config.database) as session:
                # Delete test data
                session.run("""
                    MATCH (n) 
                    WHERE (n.fsq_place_id IS NOT NULL AND n.fsq_place_id STARTS WITH 'test_')
                       OR (n.stop_id IS NOT NULL AND n.stop_id STARTS WITH 'test_')
                       OR (n.category_id IS NOT NULL AND n.category_id STARTS WITH 'test_')
                    DETACH DELETE n
                """)
                
                # Delete orphaned categories
                session.run("""
                    MATCH (c:Category) 
                    WHERE size((c)<--()) = 0
                    DELETE c
                """)
            
            driver.close()
        except Exception as e:
            print(f"Warning: Could not clean test database: {e}")
    
    # Clean before test
    cleanup()
    
    yield
    
    # Clean after test
    cleanup()


@pytest.fixture
def mock_importer(mock_neo4j_config, temp_data_dir):
    """Create mocked FoursquareImporter for unit tests"""
    with pytest.mock.patch('foursquare_import_neo4j.GraphDatabase.driver'):
        importer = FoursquareImporter(
            config=mock_neo4j_config,
            data_dir=str(temp_data_dir)
        )
        yield importer
        try:
            importer.close()
        except:
            pass


@pytest.fixture
def integration_importer(test_config, temp_data_dir, neo4j_available, clean_test_database):
    """Create real FoursquareImporter for integration tests"""
    if not neo4j_available:
        pytest.skip("Neo4j not available")
    
    importer = FoursquareImporter(
        config=test_config,
        data_dir=str(temp_data_dir)
    )
    
    yield importer
    
    try:
        importer.close()
    except:
        pass


# Pytest markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (require Neo4j)")
    config.addinivalue_line("markers", "geospatial: Geospatial tests (require Neo4j with spatial support)")
    config.addinivalue_line("markers", "slow: Slow running tests")


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on their location and requirements"""
    for item in items:
        # Mark integration tests
        if "test_integration" in str(item.fspath) or "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        
        # Mark geospatial tests
        if "geospatial" in str(item.fspath) or "spatial" in item.name.lower():
            item.add_marker(pytest.mark.geospatial)
            item.add_marker(pytest.mark.integration)  # Geospatial tests also need Neo4j
        
        # Mark unit tests (everything not marked as integration)
        if not any(marker.name == "integration" for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# Skip integration tests unless explicitly enabled
def pytest_runtest_setup(item):
    """Skip tests based on environment variables"""
    if item.get_closest_marker("integration"):
        if not os.getenv("RUN_INTEGRATION_TESTS"):
            pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to run them.")
    
    if item.get_closest_marker("slow"):
        if not os.getenv("RUN_LONG_TESTS"):
            pytest.skip("Long running tests disabled. Set RUN_LONG_TESTS=1 to run them.")