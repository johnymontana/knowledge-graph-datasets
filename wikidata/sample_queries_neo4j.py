#!/usr/bin/env python3
"""
Sample Neo4j Queries for Wikidata Knowledge Graph

This script demonstrates various query patterns and capabilities
after importing Wikidata into Neo4j.
"""

import os
import sys
import logging
from typing import List, Dict, Any
from pathlib import Path

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from neo4j_config import Neo4jConfig

logger = logging.getLogger(__name__)

class WikidataNeo4jQueries:
    """Sample queries for Wikidata knowledge graph in Neo4j"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize with Neo4j configuration"""
        self.config = Neo4jConfig(config_file)
        self.driver = self.config.get_driver()
        self.database = self.config.get_database()
        
        print(f"🔧 Connected to Neo4j: {self.config.uri}")
        print(f"📊 Database: {self.config.database}")
    
    def run_query(self, query: str, description: str = "") -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        print(f"\n🔍 {description}")
        print(f"Query: {query}")
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            records = [record.data() for record in result]
            
        print(f"✅ Found {len(records)} results")
        return records
    
    def database_overview(self):
        """Get overview of the imported data"""
        queries = [
            ("MATCH (n) RETURN labels(n) as labels, count(*) as count ORDER BY count DESC",
             "📈 Node counts by label"),
            
            ("MATCH ()-[r]->() RETURN type(r) as relationship, count(*) as count ORDER BY count DESC",
             "🔗 Relationship counts by type"),
             
            ("MATCH (n:Entity) WHERE exists(n.coordinates) RETURN count(*) as spatial_entities",
             "🌍 Entities with spatial coordinates"),
             
            ("MATCH (n:Entity) RETURN n.type as entity_type, count(*) as count ORDER BY count DESC",
             "📊 Entity counts by type")
        ]
        
        print("=" * 60)
        print("📊 DATABASE OVERVIEW")
        print("=" * 60)
        
        for query, description in queries:
            results = self.run_query(query, description)
            for record in results[:10]:  # Show top 10 results
                print(f"  {record}")
    
    def scientist_queries(self):
        """Queries focused on scientists and their relationships"""
        print("\n" + "=" * 60)
        print("👨‍🔬 SCIENTIST QUERIES")
        print("=" * 60)
        
        queries = [
            # Basic scientist information
            ("""MATCH (p:Person {occupation: 'Scientist'}) 
                RETURN p.name, p.birth_date, p.death_date 
                ORDER BY p.name LIMIT 10""",
             "🧑‍🔬 Top 10 scientists by name"),
            
            # Scientists by field
            ("""MATCH (p:Person {occupation: 'Scientist'})-[:WORKS_IN]->(f:Field)
                RETURN f.name as field, count(p) as scientist_count
                ORDER BY scientist_count DESC LIMIT 10""",
             "📚 Scientists by field of work"),
            
            # Scientists by country
            ("""MATCH (p:Person {occupation: 'Scientist'})-[:CITIZEN_OF]->(c:Country)
                RETURN c.name as country, count(p) as scientist_count
                ORDER BY scientist_count DESC LIMIT 10""",
             "🌍 Scientists by country"),
            
            # Living vs deceased scientists
            ("""MATCH (p:Person {occupation: 'Scientist'})
                RETURN 
                    CASE WHEN p.death_date IS NULL OR p.death_date = '' 
                         THEN 'Living' ELSE 'Deceased' END as status,
                    count(p) as count""",
             "⚰️ Living vs deceased scientists"),
            
            # Scientists with coordinates (spatial data)
            ("""MATCH (p:Person {occupation: 'Scientist'})
                WHERE p.coordinates IS NOT NULL
                RETURN p.name, p.coordinates.latitude as lat, p.coordinates.longitude as lon
                LIMIT 10""",
             "📍 Scientists with location data")
        ]
        
        for query, description in queries:
            results = self.run_query(query, description)
            for record in results:
                print(f"  {record}")
    
    def city_queries(self):
        """Queries focused on cities and geographic data"""
        print("\n" + "=" * 60)
        print("🏙️ CITY QUERIES")
        print("=" * 60)
        
        queries = [
            # Largest cities by population
            ("""MATCH (c:City)
                WHERE c.population IS NOT NULL AND c.population > 0
                RETURN c.name, c.population
                ORDER BY c.population DESC LIMIT 10""",
             "🏙️ Largest cities by population"),
            
            # Cities by state
            ("""MATCH (c:City)-[:LOCATED_IN]->(s:State)
                RETURN s.name as state, count(c) as city_count
                ORDER BY city_count DESC LIMIT 10""",
             "🗺️ Cities by state"),
            
            # Mayors and their cities
            ("""MATCH (m:Person)-[:MAYOR_OF]->(c:City)
                RETURN m.name as mayor, c.name as city
                ORDER BY c.population DESC LIMIT 10""",
             "👨‍💼 Mayors and their cities"),
            
            # Geographic distribution of cities
            ("""MATCH (c:City)
                WHERE c.coordinates IS NOT NULL
                RETURN count(c) as cities_with_coordinates""",
             "📍 Cities with geographic coordinates"),
            
            # Average population by state
            ("""MATCH (c:City)-[:LOCATED_IN]->(s:State)
                WHERE c.population IS NOT NULL AND c.population > 0
                RETURN s.name as state, 
                       avg(c.population) as avg_population,
                       count(c) as city_count
                ORDER BY avg_population DESC LIMIT 10""",
             "📊 Average city population by state")
        ]
        
        for query, description in queries:
            results = self.run_query(query, description)
            for record in results:
                print(f"  {record}")
    
    def university_queries(self):
        """Queries focused on universities and education"""
        print("\n" + "=" * 60)
        print("🎓 UNIVERSITY QUERIES")
        print("=" * 60)
        
        queries = [
            # Universities by country
            ("""MATCH (u:University)-[:LOCATED_IN]->(c:Country)
                RETURN c.name as country, count(u) as university_count
                ORDER BY university_count DESC LIMIT 10""",
             "🌍 Universities by country"),
            
            # Largest universities by student count
            ("""MATCH (u:University)
                WHERE u.students_count IS NOT NULL AND u.students_count > 0
                RETURN u.name, u.students_count
                ORDER BY u.students_count DESC LIMIT 10""",
             "👥 Largest universities by student count"),
            
            # Oldest universities
            ("""MATCH (u:University)
                WHERE u.founded IS NOT NULL AND u.founded <> ''
                RETURN u.name, u.founded
                ORDER BY u.founded LIMIT 10""",
             "📅 Oldest universities"),
            
            # Universities with location data
            ("""MATCH (u:University)
                WHERE u.coordinates IS NOT NULL
                RETURN u.name, u.coordinates.latitude as lat, u.coordinates.longitude as lon
                LIMIT 10""",
             "📍 Universities with location data")
        ]
        
        for query, description in queries:
            results = self.run_query(query, description)
            for record in results:
                print(f"  {record}")
    
    def company_queries(self):
        """Queries focused on companies and business entities"""
        print("\n" + "=" * 60)
        print("🏢 COMPANY QUERIES")
        print("=" * 60)
        
        queries = [
            # Companies by country
            ("""MATCH (c:Company)-[:LOCATED_IN]->(country:Country)
                RETURN country.name as country, count(c) as company_count
                ORDER BY company_count DESC LIMIT 10""",
             "🌍 Companies by country"),
            
            # Company founding years
            ("""MATCH (c:Company)
                WHERE c.founded IS NOT NULL AND c.founded <> ''
                WITH c, toInteger(substring(c.founded, 0, 4)) as founding_year
                WHERE founding_year > 1800
                RETURN founding_year, count(c) as companies_founded
                ORDER BY founding_year DESC LIMIT 10""",
             "📅 Companies by founding year"),
            
            # Companies with location data
            ("""MATCH (c:Company)
                WHERE c.coordinates IS NOT NULL
                RETURN c.name, c.coordinates.latitude as lat, c.coordinates.longitude as lon
                LIMIT 10""",
             "📍 Companies with location data")
        ]
        
        for query, description in queries:
            results = self.run_query(query, description)
            for record in results:
                print(f"  {record}")
    
    def spatial_queries(self):
        """Spatial and geographic queries"""
        print("\n" + "=" * 60)
        print("🌍 SPATIAL QUERIES")
        print("=" * 60)
        
        queries = [
            # Entities within a bounding box (example: San Francisco Bay Area)
            ("""MATCH (n:Entity)
                WHERE n.coordinates IS NOT NULL
                  AND n.coordinates.latitude > 37.0 
                  AND n.coordinates.latitude < 38.0
                  AND n.coordinates.longitude > -123.0 
                  AND n.coordinates.longitude < -121.0
                RETURN labels(n) as labels, n.name, n.coordinates
                LIMIT 10""",
             "📍 Entities in San Francisco Bay Area"),
            
            # Find entities near a specific point (example: near NYC)
            ("""MATCH (n:Entity)
                WHERE n.coordinates IS NOT NULL
                WITH n, point({latitude: 40.7128, longitude: -74.0060}) as nyc,
                     point(n.coordinates) as entity_point
                WITH n, distance(nyc, entity_point) as distance_meters
                WHERE distance_meters < 100000  // Within 100km
                RETURN n.name, n.coordinates, distance_meters
                ORDER BY distance_meters LIMIT 10""",
             "🗽 Entities near New York City"),
            
            # Count of entities with coordinates by type
            ("""MATCH (n:Entity)
                WHERE n.coordinates IS NOT NULL
                RETURN n.type as entity_type, count(n) as count
                ORDER BY count DESC""",
             "📊 Spatial entities by type")
        ]
        
        for query, description in queries:
            results = self.run_query(query, description)
            for record in results:
                print(f"  {record}")
    
    def relationship_analysis(self):
        """Analyze relationships and connections"""
        print("\n" + "=" * 60)
        print("🔗 RELATIONSHIP ANALYSIS")
        print("=" * 60)
        
        queries = [
            # Most connected entities
            ("""MATCH (n:Entity)
                WITH n, size([(n)-[]->() | 1]) + size([()-[]->(n) | 1]) as degree
                WHERE degree > 0
                RETURN n.name, n.type, degree
                ORDER BY degree DESC LIMIT 10""",
             "⭐ Most connected entities"),
            
            # Countries with most scientists
            ("""MATCH (c:Country)<-[:CITIZEN_OF]-(p:Person {occupation: 'Scientist'})
                RETURN c.name as country, count(p) as scientist_count
                ORDER BY scientist_count DESC LIMIT 10""",
             "🧑‍🔬 Countries with most scientists"),
            
            # Fields with most scientists
            ("""MATCH (f:Field)<-[:WORKS_IN]-(p:Person {occupation: 'Scientist'})
                RETURN f.name as field, count(p) as scientist_count
                ORDER BY scientist_count DESC LIMIT 10""",
             "📚 Fields with most scientists"),
            
            # Path analysis: Find connections between entities
            ("""MATCH path = (a:Person {occupation: 'Scientist'})-[*1..2]-(b:University)
                WHERE a.name CONTAINS 'Einstein'
                RETURN a.name, b.name, length(path) as path_length
                LIMIT 5""",
             "🛤️ Paths between scientists and universities")
        ]
        
        for query, description in queries:
            results = self.run_query(query, description)
            for record in results:
                print(f"  {record}")
    
    def performance_queries(self):
        """Test query performance and optimization"""
        print("\n" + "=" * 60)
        print("⚡ PERFORMANCE QUERIES")
        print("=" * 60)
        
        queries = [
            # Index usage
            ("CALL db.indexes()",
             "📋 Available indexes"),
            
            # Constraint usage
            ("CALL db.constraints()",
             "🔒 Available constraints"),
            
            # Database statistics
            ("""CALL apoc.meta.stats() YIELD labels, relTypesCount, stats
                RETURN labels, relTypesCount, stats.nodes as total_nodes, stats.relationships as total_relationships""",
             "📊 Database statistics (requires APOC)")
        ]
        
        for query, description in queries:
            try:
                results = self.run_query(query, description)
                for record in results:
                    print(f"  {record}")
            except Exception as e:
                print(f"  ⚠️ Query failed (may require APOC plugin): {e}")
    
    def run_all_queries(self):
        """Run all sample query categories"""
        print("🚀 Running all Wikidata Neo4j sample queries...")
        
        try:
            self.database_overview()
            self.scientist_queries()
            self.city_queries()
            self.university_queries()
            self.company_queries()
            self.spatial_queries()
            self.relationship_analysis()
            self.performance_queries()
            
        except Exception as e:
            logger.error(f"Error running queries: {e}")
            raise
        
        print("\n✅ All queries completed successfully!")
    
    def close(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()

def main():
    """Main function to run sample queries"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run sample queries on Wikidata Neo4j knowledge graph")
    parser.add_argument("--config-file", default="config.env", help="Configuration file path")
    parser.add_argument("--category", choices=[
        "overview", "scientists", "cities", "universities", "companies", 
        "spatial", "relationships", "performance", "all"
    ], default="all", help="Query category to run")
    
    args = parser.parse_args()
    
    # Initialize query runner
    query_runner = WikidataNeo4jQueries(args.config_file)
    
    try:
        # Run selected category
        if args.category == "all":
            query_runner.run_all_queries()
        elif args.category == "overview":
            query_runner.database_overview()
        elif args.category == "scientists":
            query_runner.scientist_queries()
        elif args.category == "cities":
            query_runner.city_queries()
        elif args.category == "universities":
            query_runner.university_queries()
        elif args.category == "companies":
            query_runner.company_queries()
        elif args.category == "spatial":
            query_runner.spatial_queries()
        elif args.category == "relationships":
            query_runner.relationship_analysis()
        elif args.category == "performance":
            query_runner.performance_queries()
            
    except Exception as e:
        logger.error(f"❌ Query execution failed: {e}")
        sys.exit(1)
        
    finally:
        query_runner.close()

if __name__ == "__main__":
    main()