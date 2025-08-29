#!/usr/bin/env python3
"""
Neo4j Schema Setup for Wikidata Knowledge Graph

This script creates the necessary constraints, indexes, and schema
for optimal performance when querying Wikidata in Neo4j.
"""

import os
import sys
import logging
from typing import List, Dict, Any

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from neo4j_config import Neo4jConfig

logger = logging.getLogger(__name__)

class WikidataSchema:
    """Schema management for Wikidata Neo4j knowledge graph"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize with Neo4j configuration"""
        self.config = Neo4jConfig(config_file)
        self.driver = self.config.get_driver()
        self.database = self.config.get_database()
        
        print(f"🔧 Connected to Neo4j: {self.config.uri}")
        print(f"📊 Database: {self.config.database}")
    
    def create_constraints(self):
        """Create uniqueness constraints for key properties"""
        print("🔒 Creating uniqueness constraints...")
        
        constraints = [
            # Entity constraints
            "CREATE CONSTRAINT wikidata_entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.wikidata_id IS UNIQUE",
            
            # Person constraints
            "CREATE CONSTRAINT person_wikidata_id IF NOT EXISTS FOR (p:Person) REQUIRE p.wikidata_id IS UNIQUE",
            
            # Place constraints
            "CREATE CONSTRAINT place_wikidata_id IF NOT EXISTS FOR (p:Place) REQUIRE p.wikidata_id IS UNIQUE",
            "CREATE CONSTRAINT city_wikidata_id IF NOT EXISTS FOR (c:City) REQUIRE c.wikidata_id IS UNIQUE",
            "CREATE CONSTRAINT state_wikidata_id IF NOT EXISTS FOR (s:State) REQUIRE s.wikidata_id IS UNIQUE",
            "CREATE CONSTRAINT country_wikidata_id IF NOT EXISTS FOR (c:Country) REQUIRE c.wikidata_id IS UNIQUE",
            
            # Organization constraints
            "CREATE CONSTRAINT organization_wikidata_id IF NOT EXISTS FOR (o:Organization) REQUIRE o.wikidata_id IS UNIQUE",
            "CREATE CONSTRAINT university_wikidata_id IF NOT EXISTS FOR (u:University) REQUIRE u.wikidata_id IS UNIQUE",
            "CREATE CONSTRAINT company_wikidata_id IF NOT EXISTS FOR (c:Company) REQUIRE c.wikidata_id IS UNIQUE",
            
            # Other entity constraints
            "CREATE CONSTRAINT field_name IF NOT EXISTS FOR (f:Field) REQUIRE f.name IS UNIQUE",
        ]
        
        created_count = 0
        with self.driver.session(database=self.database) as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    created_count += 1
                    logger.debug(f"Created constraint: {constraint}")
                except Exception as e:
                    if "already exists" not in str(e).lower() and "equivalent" not in str(e).lower():
                        logger.warning(f"Failed to create constraint: {constraint} - {e}")
        
        print(f"✅ Processed {created_count} constraints")
    
    def create_indexes(self):
        """Create indexes for improved query performance"""
        print("📋 Creating performance indexes...")
        
        indexes = [
            # Label-based indexes
            "CREATE INDEX entity_label_idx IF NOT EXISTS FOR (e:Entity) ON (e.label)",
            "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            
            # Person indexes
            "CREATE INDEX person_name_idx IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX person_occupation_idx IF NOT EXISTS FOR (p:Person) ON (p.occupation)",
            "CREATE INDEX person_birth_date_idx IF NOT EXISTS FOR (p:Person) ON (p.birth_date)",
            "CREATE INDEX person_death_date_idx IF NOT EXISTS FOR (p:Person) ON (p.death_date)",
            
            # Place indexes
            "CREATE INDEX place_name_idx IF NOT EXISTS FOR (p:Place) ON (p.name)",
            "CREATE INDEX city_name_idx IF NOT EXISTS FOR (c:City) ON (c.name)",
            "CREATE INDEX city_population_idx IF NOT EXISTS FOR (c:City) ON (c.population)",
            "CREATE INDEX country_name_idx IF NOT EXISTS FOR (c:Country) ON (c.name)",
            "CREATE INDEX state_name_idx IF NOT EXISTS FOR (s:State) ON (s.name)",
            
            # Organization indexes
            "CREATE INDEX organization_name_idx IF NOT EXISTS FOR (o:Organization) ON (o.name)",
            "CREATE INDEX university_name_idx IF NOT EXISTS FOR (u:University) ON (u.name)",
            "CREATE INDEX university_founded_idx IF NOT EXISTS FOR (u:University) ON (u.founded)",
            "CREATE INDEX university_students_idx IF NOT EXISTS FOR (u:University) ON (u.students_count)",
            "CREATE INDEX company_name_idx IF NOT EXISTS FOR (c:Company) ON (c.name)",
            "CREATE INDEX company_founded_idx IF NOT EXISTS FOR (c:Company) ON (c.founded)",
            
            # Field indexes
            "CREATE INDEX field_name_idx IF NOT EXISTS FOR (f:Field) ON (f.name)",
            
            # Full-text search indexes
            "CREATE FULLTEXT INDEX entity_fulltext_idx IF NOT EXISTS FOR (e:Entity) ON EACH [e.name, e.label, e.description]",
            "CREATE FULLTEXT INDEX person_fulltext_idx IF NOT EXISTS FOR (p:Person) ON EACH [p.name, p.label]",
            "CREATE FULLTEXT INDEX place_fulltext_idx IF NOT EXISTS FOR (p:Place) ON EACH [p.name, p.label]",
            "CREATE FULLTEXT INDEX organization_fulltext_idx IF NOT EXISTS FOR (o:Organization) ON EACH [o.name, o.label]",
        ]
        
        created_count = 0
        with self.driver.session(database=self.database) as session:
            for index in indexes:
                try:
                    session.run(index)
                    created_count += 1
                    logger.debug(f"Created index: {index}")
                except Exception as e:
                    if "already exists" not in str(e).lower() and "equivalent" not in str(e).lower():
                        logger.warning(f"Failed to create index: {index} - {e}")
        
        print(f"✅ Processed {created_count} indexes")
    
    def create_spatial_indexes(self):
        """Create spatial indexes for geographic queries"""
        print("🌍 Creating spatial indexes...")
        
        spatial_indexes = [
            # Point indexes for coordinates
            "CREATE POINT INDEX entity_coordinates_idx IF NOT EXISTS FOR (e:Entity) ON (e.coordinates)",
            "CREATE POINT INDEX person_coordinates_idx IF NOT EXISTS FOR (p:Person) ON (p.coordinates)",
            "CREATE POINT INDEX place_coordinates_idx IF NOT EXISTS FOR (p:Place) ON (p.coordinates)",
            "CREATE POINT INDEX city_coordinates_idx IF NOT EXISTS FOR (c:City) ON (c.coordinates)",
            "CREATE POINT INDEX university_coordinates_idx IF NOT EXISTS FOR (u:University) ON (u.coordinates)",
            "CREATE POINT INDEX company_coordinates_idx IF NOT EXISTS FOR (c:Company) ON (c.coordinates)",
        ]
        
        created_count = 0
        with self.driver.session(database=self.database) as session:
            for index in spatial_indexes:
                try:
                    session.run(index)
                    created_count += 1
                    logger.debug(f"Created spatial index: {index}")
                except Exception as e:
                    if "already exists" not in str(e).lower() and "equivalent" not in str(e).lower():
                        logger.warning(f"Failed to create spatial index: {index} - {e}")
        
        print(f"✅ Processed {created_count} spatial indexes")
    
    def create_composite_indexes(self):
        """Create composite indexes for complex queries"""
        print("🔗 Creating composite indexes...")
        
        composite_indexes = [
            # Multi-property indexes for common query patterns
            "CREATE INDEX person_occupation_country_idx IF NOT EXISTS FOR (p:Person) ON (p.occupation, p.country)",
            "CREATE INDEX city_state_population_idx IF NOT EXISTS FOR (c:City) ON (c.state, c.population)",
            "CREATE INDEX university_country_students_idx IF NOT EXISTS FOR (u:University) ON (u.country, u.students_count)",
            "CREATE INDEX company_country_founded_idx IF NOT EXISTS FOR (c:Company) ON (c.country, c.founded)",
            
            # Date-based composite indexes
            "CREATE INDEX person_birth_death_idx IF NOT EXISTS FOR (p:Person) ON (p.birth_date, p.death_date)",
        ]
        
        created_count = 0
        with self.driver.session(database=self.database) as session:
            for index in composite_indexes:
                try:
                    session.run(index)
                    created_count += 1
                    logger.debug(f"Created composite index: {index}")
                except Exception as e:
                    if "already exists" not in str(e).lower() and "equivalent" not in str(e).lower():
                        logger.warning(f"Failed to create composite index: {index} - {e}")
        
        print(f"✅ Processed {created_count} composite indexes")
    
    def show_schema_info(self):
        """Display information about the current schema"""
        print("\n📊 SCHEMA INFORMATION")
        print("=" * 50)
        
        with self.driver.session(database=self.database) as session:
            # Show constraints
            print("\n🔒 CONSTRAINTS:")
            try:
                result = session.run("CALL db.constraints()")
                constraints = [record["description"] for record in result]
                for i, constraint in enumerate(constraints, 1):
                    print(f"  {i}. {constraint}")
                if not constraints:
                    print("  No constraints found")
            except Exception as e:
                print(f"  Error retrieving constraints: {e}")
            
            # Show indexes
            print("\n📋 INDEXES:")
            try:
                result = session.run("CALL db.indexes()")
                indexes = [{"name": record["name"], "type": record["type"], "state": record["state"]} 
                          for record in result]
                for i, index in enumerate(indexes, 1):
                    status = "✅" if index["state"] == "ONLINE" else "⚠️"
                    print(f"  {i}. {status} {index['name']} ({index['type']})")
                if not indexes:
                    print("  No indexes found")
            except Exception as e:
                print(f"  Error retrieving indexes: {e}")
            
            # Show node labels
            print("\n🏷️ NODE LABELS:")
            try:
                result = session.run("CALL db.labels()")
                labels = [record["label"] for record in result]
                for i, label in enumerate(sorted(labels), 1):
                    print(f"  {i}. {label}")
                if not labels:
                    print("  No labels found")
            except Exception as e:
                print(f"  Error retrieving labels: {e}")
            
            # Show relationship types
            print("\n🔗 RELATIONSHIP TYPES:")
            try:
                result = session.run("CALL db.relationshipTypes()")
                rel_types = [record["relationshipType"] for record in result]
                for i, rel_type in enumerate(sorted(rel_types), 1):
                    print(f"  {i}. {rel_type}")
                if not rel_types:
                    print("  No relationship types found")
            except Exception as e:
                print(f"  Error retrieving relationship types: {e}")
    
    def optimize_for_wikidata(self):
        """Apply Wikidata-specific optimizations"""
        print("⚡ Applying Wikidata-specific optimizations...")
        
        with self.driver.session(database=self.database) as session:
            # Update statistics to help query planner
            try:
                session.run("CALL db.stats.collect()")
                print("✅ Updated database statistics")
            except Exception as e:
                logger.warning(f"Failed to update statistics: {e}")
            
            # Warm up the page cache by loading commonly accessed data
            warmup_queries = [
                "MATCH (n:Entity) RETURN count(n)",
                "MATCH (p:Person) RETURN count(p)",
                "MATCH (c:City) RETURN count(c)",
                "MATCH ()-[r]->() RETURN count(r)",
            ]
            
            for query in warmup_queries:
                try:
                    session.run(query)
                    logger.debug(f"Warmed up cache with: {query}")
                except Exception as e:
                    logger.warning(f"Warmup query failed: {query} - {e}")
            
            print("✅ Cache warmup completed")
    
    def create_all_schema(self):
        """Create complete schema for Wikidata knowledge graph"""
        print("🏗️ Creating complete Wikidata schema...")
        print("=" * 60)
        
        try:
            self.create_constraints()
            self.create_indexes()
            self.create_spatial_indexes()
            self.create_composite_indexes()
            self.optimize_for_wikidata()
            
            print("\n✅ Schema creation completed successfully!")
            
            # Show final schema information
            self.show_schema_info()
            
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            raise
    
    def drop_schema(self):
        """Drop all schema elements (use with caution!)"""
        print("⚠️ Dropping all schema elements...")
        
        with self.driver.session(database=self.database) as session:
            # Drop all indexes
            try:
                result = session.run("CALL db.indexes()")
                indexes = [record["name"] for record in result if record["name"]]
                for index_name in indexes:
                    try:
                        session.run(f"DROP INDEX {index_name}")
                        print(f"Dropped index: {index_name}")
                    except Exception as e:
                        logger.warning(f"Failed to drop index {index_name}: {e}")
            except Exception as e:
                logger.error(f"Failed to list indexes: {e}")
            
            # Drop all constraints
            try:
                result = session.run("CALL db.constraints()")
                constraints = [record["name"] for record in result if record["name"]]
                for constraint_name in constraints:
                    try:
                        session.run(f"DROP CONSTRAINT {constraint_name}")
                        print(f"Dropped constraint: {constraint_name}")
                    except Exception as e:
                        logger.warning(f"Failed to drop constraint {constraint_name}: {e}")
            except Exception as e:
                logger.error(f"Failed to list constraints: {e}")
        
        print("✅ Schema drop completed")
    
    def close(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()

def main():
    """Main function to manage Wikidata schema"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage Neo4j schema for Wikidata knowledge graph")
    parser.add_argument("--config-file", default="config.env", help="Configuration file path")
    parser.add_argument("--action", choices=["create", "show", "drop"], default="create",
                       help="Schema action to perform")
    
    args = parser.parse_args()
    
    # Initialize schema manager
    schema_manager = WikidataSchema(args.config_file)
    
    try:
        if args.action == "create":
            schema_manager.create_all_schema()
        elif args.action == "show":
            schema_manager.show_schema_info()
        elif args.action == "drop":
            confirm = input("⚠️ This will drop all schema elements. Are you sure? (yes/no): ")
            if confirm.lower() == "yes":
                schema_manager.drop_schema()
            else:
                print("Operation cancelled")
                
    except Exception as e:
        logger.error(f"❌ Schema operation failed: {e}")
        sys.exit(1)
        
    finally:
        schema_manager.close()

if __name__ == "__main__":
    main()