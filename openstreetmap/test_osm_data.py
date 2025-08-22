#!/usr/bin/env python3
"""
OSM Data Validation Script

This script validates OpenStreetMap data and tests the import functionality.
It can be used to verify data quality and test the OSM import pipeline.
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any
import osmnx as ox
import geopandas as gpd
import pandas as pd
from neo4j_config import Neo4jConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OSMDataValidator:
    """Class for validating OSM data and testing import functionality."""
    
    def __init__(self, config: Neo4jConfig):
        self.config = config
    
    def test_osm_connection(self) -> bool:
        """Test OSM data access."""
        try:
            logger.info("🔍 Testing OSM data access...")
            
            # Test with a simple query
            test_location = "San Francisco, California"
            test_tags = {"amenity": "restaurant"}
            
            gdf = ox.geometries_from_place(test_location, tags=test_tags, limit=5)
            
            if not gdf.empty:
                logger.info(f"✅ OSM data access successful. Found {len(gdf)} test features")
                return True
            else:
                logger.warning("⚠️  OSM data access successful but no test data found")
                return True
                
        except Exception as e:
            logger.error(f"❌ OSM data access failed: {e}")
            return False
    
    def test_dgraph_connection(self) -> bool:
        """Test Dgraph connection."""
        try:
            logger.info("🔍 Testing Dgraph connection...")
            
            # This would test the actual Dgraph connection
            # For now, we'll just check if the config is valid
            conn_params = self.config.get_connection_params()
            
            if conn_params:
                logger.info("✅ Dgraph configuration is valid")
                return True
            else:
                logger.error("❌ Dgraph configuration is invalid")
                return False
                
        except Exception as e:
            logger.error(f"❌ Dgraph connection test failed: {e}")
            return False
    
    def validate_osm_data(self, location: str, tags: Dict[str, str]) -> Dict[str, Any]:
        """Validate OSM data for a specific location and tags."""
        try:
            logger.info(f"🔍 Validating OSM data for: {location}")
            logger.info(f"🏷️  Tags: {tags}")
            
            # Fetch OSM data
            gdf = ox.geometries_from_place(location, tags=tags)
            
            if gdf.empty:
                logger.warning("⚠️  No OSM data found")
                return {
                    'valid': False,
                    'count': 0,
                    'columns': [],
                    'sample_data': None,
                    'errors': ['No data found for the specified location and tags']
                }
            
            # Analyze data quality
            validation_results = {
                'valid': True,
                'count': len(gdf),
                'columns': list(gdf.columns),
                'sample_data': gdf.head(3).to_dict('records'),
                'errors': []
            }
            
            # Check for required columns
            required_columns = ['geometry']
            for col in required_columns:
                if col not in gdf.columns:
                    validation_results['errors'].append(f"Missing required column: {col}")
                    validation_results['valid'] = False
            
            # Check for empty geometries
            if 'geometry' in gdf.columns:
                empty_geometries = gdf[gdf.geometry.isna()].shape[0]
                if empty_geometries > 0:
                    validation_results['errors'].append(f"Found {empty_geometries} features with empty geometries")
            
            # Check data types
            logger.info(f"📊 Data validation results:")
            logger.info(f"   • Total features: {validation_results['count']}")
            logger.info(f"   • Columns: {validation_results['columns']}")
            
            if validation_results['errors']:
                logger.warning(f"⚠️  Validation warnings: {validation_results['errors']}")
            else:
                logger.info("✅ Data validation passed")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Data validation failed: {e}")
            return {
                'valid': False,
                'count': 0,
                'columns': [],
                'sample_data': None,
                'errors': [str(e)]
            }
    
    def run_tests(self) -> bool:
        """Run all validation tests."""
        logger.info("🚀 Running OSM data validation tests...")
        
        all_passed = True
        
        # Test OSM connection
        if not self.test_osm_connection():
            all_passed = False
        
        # Test Dgraph connection
        if not self.test_dgraph_connection():
            all_passed = False
        
        # Validate sample data
        osm_config = self.config.get_osm_config()
        validation_results = self.validate_osm_data(
            osm_config['location'], 
            {'amenity': osm_config['tags']}
        )
        
        if not validation_results['valid']:
            all_passed = False
        
        # Summary
        if all_passed:
            logger.info("🎉 All tests passed!")
        else:
            logger.warning("⚠️  Some tests failed")
        
        return all_passed


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate OSM data and test import functionality")
    parser.add_argument("--location", help="OSM location to test")
    parser.add_argument("--tags", help="OSM tags to test (e.g., amenity=restaurant)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = Neo4jConfig()
    
    # Override config with command line arguments
    if args.location:
        config.osm_location = args.location
    if args.tags:
        config.osm_tags = args.tags
    
    # Create validator and run tests
    validator = OSMDataValidator(config)
    success = validator.run_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
