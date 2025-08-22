#!/usr/bin/env python3
"""
Tests for OSM Import functionality

This module contains tests for the OpenStreetMap import functionality.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dgraph_config import DgraphConfig
from osm_import import OSMImporter


class TestDgraphConfig:
    """Test DgraphConfig class."""
    
    def test_config_initialization(self):
        """Test configuration initialization."""
        config = DgraphConfig()
        assert config.batch_size == 1000
        assert config.data_dir == 'data'
        assert 'San Francisco' in config.osm_location
        assert config.osm_tags == 'amenity=restaurant'
    
    def test_connection_params_local(self):
        """Test local connection parameters."""
        config = DgraphConfig()
        config.connection_string = "@dgraph://localhost:8080"
        params = config.get_connection_params()
        assert params['host'] == 'localhost'
        assert params['port'] == 8080
    
    def test_osm_config(self):
        """Test OSM configuration retrieval."""
        config = DgraphConfig()
        osm_config = config.get_osm_config()
        assert 'location' in osm_config
        assert 'tags' in osm_config
        assert 'output_file' in osm_config


class TestOSMImporter:
    """Test OSMImporter class."""
    
    @patch('osm_import.ox.geometries_from_place')
    def test_search_osm_data_success(self, mock_geometries):
        """Test successful OSM data search."""
        # Mock successful response
        mock_gdf = Mock()
        mock_gdf.empty = False
        mock_gdf.__len__ = Mock(return_value=5)
        mock_geometries.return_value = mock_gdf
        
        config = DgraphConfig()
        importer = OSMImporter(config)
        
        result = importer.search_osm_data("Test Location", {"amenity": "restaurant"})
        assert not result.empty
        assert len(result) == 5
    
    @patch('osm_import.ox.geometries_from_place')
    def test_search_osm_data_empty(self, mock_geometries):
        """Test OSM data search with no results."""
        # Mock empty response
        mock_gdf = Mock()
        mock_gdf.empty = True
        mock_geometries.return_value = mock_gdf
        
        config = DgraphConfig()
        importer = OSMImporter(config)
        
        result = importer.search_osm_data("Test Location", {"amenity": "restaurant"})
        assert result.empty
    
    def test_convert_to_rdf(self):
        """Test RDF conversion."""
        config = DgraphConfig()
        importer = OSMImporter(config)
        
        # Create mock GeoDataFrame
        mock_gdf = Mock()
        mock_gdf.iterrows.return_value = [
            (0, Mock(geometry=Mock(wkt="POINT(0 0)"), amenity="restaurant", name="Test Restaurant"))
        ]
        mock_gdf.columns = ['geometry', 'amenity', 'name']
        
        result = importer.convert_to_rdf(mock_gdf)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__])
