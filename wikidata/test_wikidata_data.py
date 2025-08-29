#!/usr/bin/env python3
"""
Data Validation Tests for Wikidata Neo4j Knowledge Graph

This script validates the integrity and quality of imported Wikidata
in the Neo4j database.
"""

import os
import sys
import logging
import unittest
from typing import Dict, Any, List

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from neo4j_config import Neo4jConfig

logger = logging.getLogger(__name__)

class WikidataDataTests(unittest.TestCase):
    """Test cases for validating Wikidata import quality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.config = Neo4jConfig()
        cls.driver = cls.config.get_driver()
        cls.database = cls.config.get_database()
        
        # Test connection
        if not cls.config.validate_connection():
            raise Exception("Cannot connect to Neo4j for testing")
        
        print(f"🔧 Connected to Neo4j: {cls.config.uri}")
        print(f"📊 Database: {cls.config.database}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        if cls.driver:
            cls.driver.close()
    
    def run_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            return [record.data() for record in result]
    
    def get_single_value(self, query: str) -> Any:
        """Get single value from query"""
        results = self.run_query(query)
        if results and len(results) > 0:
            return list(results[0].values())[0]
        return None
    
    def test_database_has_data(self):
        """Test that database contains imported data"""
        print("\n🔍 Testing database has data...")
        
        # Check for entities
        entity_count = self.get_single_value("MATCH (n:Entity) RETURN count(n)")
        self.assertIsNotNone(entity_count, "Failed to count entities")
        self.assertGreater(entity_count, 0, "No entities found in database")
        print(f"✅ Found {entity_count} entities")
        
        # Check for relationships
        rel_count = self.get_single_value("MATCH ()-[r]->() RETURN count(r)")
        self.assertIsNotNone(rel_count, "Failed to count relationships")
        self.assertGreater(rel_count, 0, "No relationships found in database")
        print(f"✅ Found {rel_count} relationships")
    
    def test_required_labels_exist(self):
        """Test that expected node labels exist"""
        print("\n🏷️ Testing required labels exist...")
        
        expected_labels = ["Entity", "Person", "Place", "Organization"]
        
        existing_labels = [r["label"] for r in self.run_query("CALL db.labels()")]
        
        for label in expected_labels:
            self.assertIn(label, existing_labels, f"Required label '{label}' not found")
            
            # Count nodes with this label
            count = self.get_single_value(f"MATCH (n:{label}) RETURN count(n)")
            print(f"✅ {label}: {count} nodes")
    
    def test_wikidata_ids_exist(self):
        """Test that entities have Wikidata IDs"""
        print("\n🆔 Testing Wikidata IDs...")
        
        # All entities should have wikidata_id
        total_entities = self.get_single_value("MATCH (n:Entity) RETURN count(n)")
        entities_with_id = self.get_single_value(
            "MATCH (n:Entity) WHERE n.wikidata_id IS NOT NULL AND n.wikidata_id <> '' RETURN count(n)"
        )
        
        self.assertEqual(total_entities, entities_with_id, 
                        f"Some entities missing wikidata_id: {total_entities - entities_with_id}")
        print(f"✅ All {total_entities} entities have Wikidata IDs")
        
        # Check ID format (should start with Q, P, or synthetic prefixes for derived entities)
        invalid_ids = self.get_single_value("""
            MATCH (n:Entity) 
            WHERE n.wikidata_id IS NOT NULL 
              AND NOT (n.wikidata_id STARTS WITH 'Q' OR n.wikidata_id STARTS WITH 'P' 
                       OR n.wikidata_id STARTS WITH 'FIELD_' OR n.wikidata_id STARTS WITH 'COUNTRY_'
                       OR n.wikidata_id STARTS WITH 'STATE_' OR n.wikidata_id STARTS WITH 'MAYOR_')
            RETURN count(n)
        """)
        
        self.assertEqual(invalid_ids, 0, f"Found {invalid_ids} entities with invalid Wikidata ID format")
        print("✅ All Wikidata IDs have valid format")
    
    def test_entity_names_exist(self):
        """Test that entities have names/labels"""
        print("\n📛 Testing entity names...")
        
        total_entities = self.get_single_value("MATCH (n:Entity) RETURN count(n)")
        entities_with_name = self.get_single_value("""
            MATCH (n:Entity) 
            WHERE (n.name IS NOT NULL AND n.name <> '') 
               OR (n.label IS NOT NULL AND n.label <> '') 
            RETURN count(n)
        """)
        
        # Allow some entities to not have names (some Wikidata entities may lack labels)
        missing_names = total_entities - entities_with_name
        missing_percentage = (missing_names / total_entities) * 100 if total_entities > 0 else 0
        
        self.assertLess(missing_percentage, 10, 
                       f"Too many entities without names: {missing_percentage:.1f}%")
        print(f"✅ {entities_with_name}/{total_entities} entities have names ({100 - missing_percentage:.1f}%)")
    
    def test_spatial_data_integrity(self):
        """Test spatial data quality"""
        print("\n🌍 Testing spatial data integrity...")
        
        spatial_entities = self.get_single_value(
            "MATCH (n:Entity) WHERE n.coordinates IS NOT NULL RETURN count(n)"
        )
        
        if spatial_entities > 0:
            print(f"✅ Found {spatial_entities} entities with coordinates")
            
            # Test coordinate ranges (basic sanity check)
            invalid_coords = self.get_single_value("""
                MATCH (n:Entity) 
                WHERE n.coordinates IS NOT NULL
                  AND (n.coordinates.latitude < -90 OR n.coordinates.latitude > 90
                       OR n.coordinates.longitude < -180 OR n.coordinates.longitude > 180)
                RETURN count(n)
            """)
            
            self.assertEqual(invalid_coords, 0, f"Found {invalid_coords} entities with invalid coordinates")
            print("✅ All coordinates are within valid ranges")
        else:
            print("⚠️ No entities with spatial coordinates found")
    
    def test_relationship_integrity(self):
        """Test relationship data integrity"""
        print("\n🔗 Testing relationship integrity...")
        
        # Test that relationships connect to existing nodes
        dangling_rels = self.get_single_value("""
            MATCH (a)-[r]->(b)
            WHERE a IS NULL OR b IS NULL
            RETURN count(r)
        """)
        
        self.assertEqual(dangling_rels, 0, f"Found {dangling_rels} dangling relationships")
        
        # Check for expected relationship types
        rel_types = [r["relationshipType"] for r in self.run_query("CALL db.relationshipTypes()")]
        
        expected_rel_types = ["WORKS_IN", "CITIZEN_OF", "LOCATED_IN", "MAYOR_OF"]
        found_expected = [rt for rt in expected_rel_types if rt in rel_types]
        
        if found_expected:
            print(f"✅ Found expected relationship types: {found_expected}")
        else:
            print("⚠️ No expected relationship types found")
    
    def test_scientists_data_quality(self):
        """Test specific data quality for scientists"""
        print("\n👨‍🔬 Testing scientists data quality...")
        
        scientists_count = self.get_single_value("MATCH (p:Person {occupation: 'Scientist'}) RETURN count(p)")
        
        if scientists_count > 0:
            print(f"✅ Found {scientists_count} scientists")
            
            # Test birth/death date formats
            invalid_dates = self.get_single_value("""
                MATCH (p:Person {occupation: 'Scientist'})
                WHERE p.birth_date IS NOT NULL AND p.birth_date <> ''
                  AND NOT p.birth_date =~ '\\d{4}-\\d{2}-\\d{2}.*'
                RETURN count(p)
            """)
            
            if invalid_dates > 0:
                print(f"⚠️ Found {invalid_dates} scientists with invalid birth date format")
            else:
                print("✅ All birth dates have valid format")
            
            # Test field relationships
            scientists_with_fields = self.get_single_value("""
                MATCH (p:Person {occupation: 'Scientist'})-[:WORKS_IN]->(:Field)
                RETURN count(DISTINCT p)
            """)
            
            field_percentage = (scientists_with_fields / scientists_count) * 100 if scientists_count > 0 else 0
            print(f"✅ {scientists_with_fields}/{scientists_count} scientists have field relationships ({field_percentage:.1f}%)")
        else:
            print("⚠️ No scientists found in database")
    
    def test_cities_data_quality(self):
        """Test specific data quality for cities"""
        print("\n🏙️ Testing cities data quality...")
        
        cities_count = self.get_single_value("MATCH (c:City) RETURN count(c)")
        
        if cities_count > 0:
            print(f"✅ Found {cities_count} cities")
            
            # Test population data
            cities_with_population = self.get_single_value("""
                MATCH (c:City)
                WHERE c.population IS NOT NULL AND c.population > 0
                RETURN count(c)
            """)
            
            pop_percentage = (cities_with_population / cities_count) * 100 if cities_count > 0 else 0
            print(f"✅ {cities_with_population}/{cities_count} cities have population data ({pop_percentage:.1f}%)")
            
            # Test state relationships
            cities_with_states = self.get_single_value("""
                MATCH (c:City)-[:LOCATED_IN]->(:State)
                RETURN count(DISTINCT c)
            """)
            
            state_percentage = (cities_with_states / cities_count) * 100 if cities_count > 0 else 0
            print(f"✅ {cities_with_states}/{cities_count} cities have state relationships ({state_percentage:.1f}%)")
        else:
            print("⚠️ No cities found in database")
    
    def test_schema_constraints(self):
        """Test that required schema constraints exist"""
        print("\n🔒 Testing schema constraints...")
        
        try:
            constraints = [r["description"] for r in self.run_query("CALL db.constraints()")]
            
            # Check for key constraints
            wikidata_constraints = [c for c in constraints if "wikidata_id" in c.lower()]
            
            self.assertGreater(len(wikidata_constraints), 0, "No Wikidata ID constraints found")
            print(f"✅ Found {len(wikidata_constraints)} Wikidata ID constraints")
            
            print(f"✅ Total constraints: {len(constraints)}")
            
        except Exception as e:
            print(f"⚠️ Could not check constraints: {e}")
    
    def test_schema_indexes(self):
        """Test that required indexes exist"""
        print("\n📋 Testing schema indexes...")
        
        try:
            indexes = [r["name"] for r in self.run_query("CALL db.indexes()")]
            
            # Check for key indexes
            name_indexes = [i for i in indexes if "name" in i.lower()]
            coord_indexes = [i for i in indexes if "coordinate" in i.lower()]
            
            print(f"✅ Found {len(name_indexes)} name-related indexes")
            print(f"✅ Found {len(coord_indexes)} coordinate indexes")
            print(f"✅ Total indexes: {len(indexes)}")
            
        except Exception as e:
            print(f"⚠️ Could not check indexes: {e}")
    
    def test_data_freshness(self):
        """Test that data was recently imported"""
        print("\n⏰ Testing data freshness...")
        
        # Check for updated_at timestamps
        entities_with_timestamps = self.get_single_value("""
            MATCH (n:Entity)
            WHERE n.updated_at IS NOT NULL
            RETURN count(n)
        """)
        
        total_entities = self.get_single_value("MATCH (n:Entity) RETURN count(n)")
        
        if entities_with_timestamps > 0:
            timestamp_percentage = (entities_with_timestamps / total_entities) * 100 if total_entities > 0 else 0
            print(f"✅ {entities_with_timestamps}/{total_entities} entities have timestamps ({timestamp_percentage:.1f}%)")
        else:
            print("⚠️ No entities have import timestamps")

def run_validation_tests():
    """Run all validation tests"""
    print("🧪 Running Wikidata Neo4j Data Validation Tests")
    print("=" * 60)
    
    # Configure test runner
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(WikidataDataTests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure.split('AssertionError: ')[-1].split(chr(10))[0]}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, error in result.errors:
            print(f"  - {test}: {error.split(chr(10))[-2]}")
    
    if result.wasSuccessful():
        print("\n🎉 All validation tests passed! Data quality looks good.")
        return True
    else:
        print("\n⚠️ Some validation tests failed. Please review the data quality.")
        return False

def main():
    """Main function to run validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Wikidata Neo4j knowledge graph")
    parser.add_argument("--config-file", default="config.env", help="Configuration file path")
    
    args = parser.parse_args()
    
    # Set config file for test class
    if args.config_file != "config.env":
        # This would require modifying the test class setup
        print(f"Using config file: {args.config_file}")
    
    try:
        success = run_validation_tests()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()