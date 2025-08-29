#!/usr/bin/env python3
"""
Sample Neo4j Queries for Diffbot Knowledge Graph Data

This script demonstrates various queries you can run against the imported
Diffbot knowledge graph data in Neo4j.
"""

import os
import sys
from typing import List, Dict, Any
from neo4j_config import Neo4jConfig

def run_sample_queries(config_file: str = "config.env"):
    """Run sample queries against Diffbot data in Neo4j"""
    
    config = Neo4jConfig(config_file)
    driver = config.get_driver()
    
    print("🔍 Running sample queries on Diffbot knowledge graph...")
    print("=" * 60)
    
    with driver.session(database=config.database) as session:
        
        # Query 1: Get database statistics
        print("\n1️⃣ Database Statistics")
        print("-" * 30)
        stats_query = """
        MATCH (n:Entity)
        RETURN 
            count(n) as total_entities,
            collect(DISTINCT n.type) as entity_types
        """
        
        result = session.run(stats_query)
        record = result.single()
        if record:
                    print(f"   Total entities: {record['total_entities']}")
        print(f"   Entity types: {', '.join(record['entity_types'])}")
        
        # Get relationship count separately
        rel_query = "MATCH ()-[r]-() RETURN count(r) as total_relationships"
        rel_result = session.run(rel_query)
        rel_record = rel_result.single()
        if rel_record:
            print(f"   Total relationships: {rel_record['total_relationships']}")
        
        # Query 2: Top organizations by name
        print("\n2️⃣ Sample Organizations")
        print("-" * 30)
        orgs_query = """
        MATCH (o:Organization)
        RETURN o.name, o.description, o.industry, o.employees
        ORDER BY o.employees DESC
        LIMIT 10
        """
        
        results = session.run(orgs_query)
        for i, record in enumerate(results, 1):
            name = record['o.name'] or 'N/A'
            industry = record['o.industry'] or ['N/A']
            employees = record['o.employees'] or 'N/A'
            print(f"   {i}. {name}")
            print(f"      Industry: {', '.join(industry) if isinstance(industry, list) else industry}")
            print(f"      Employees: {employees}")
        
        # Query 3: Sample people
        print("\n3️⃣ Sample People")
        print("-" * 30)
        people_query = """
        MATCH (p:Person)
        RETURN p.name, p.description, p.occupations, p.nationality
        LIMIT 10
        """
        
        results = session.run(people_query)
        for i, record in enumerate(results, 1):
            name = record['p.name'] or 'N/A'
            occupations = record['p.occupations'] or ['N/A']
            nationality = record['p.nationality'] or 'N/A'
            print(f"   {i}. {name}")
            print(f"      Occupations: {', '.join(occupations) if isinstance(occupations, list) else occupations}")
            print(f"      Nationality: {nationality}")
        
        # Query 4: Recent articles
        print("\n4️⃣ Recent Articles")
        print("-" * 30)
        articles_query = """
        MATCH (a:Article)
        WHERE a.published_date IS NOT NULL
        RETURN a.title, a.site_name, a.published_date, a.url
        ORDER BY a.published_date DESC
        LIMIT 5
        """
        
        results = session.run(articles_query)
        for i, record in enumerate(results, 1):
            title = record['a.title'] or 'N/A'
            site = record['a.site_name'] or 'N/A'
            date = record['a.published_date'] or 'N/A'
            url = record['a.url'] or 'N/A'
            print(f"   {i}. {title}")
            print(f"      Site: {site} | Date: {date}")
            print(f"      URL: {url}")
        
        # Query 5: Entities with locations
        print("\n5️⃣ Entities with Geographic Locations")
        print("-" * 30)
        location_query = """
        MATCH (e:Entity)
        WHERE e.location IS NOT NULL
        RETURN e.name, e.type, e.location.latitude as lat, e.location.longitude as lon
        LIMIT 10
        """
        
        results = session.run(location_query)
        for i, record in enumerate(results, 1):
            name = record['e.name'] or 'N/A'
            entity_type = record['e.type'] or 'N/A'
            lat = record['lat']
            lon = record['lon']
            print(f"   {i}. {name} ({entity_type})")
            print(f"      Location: {lat:.4f}, {lon:.4f}")
        
        # Query 6: Entity distribution by type
        print("\n6️⃣ Entity Distribution by Type")
        print("-" * 30)
        distribution_query = """
        MATCH (e:Entity)
        RETURN e.type as entity_type, count(e) as count
        ORDER BY count DESC
        """
        
        results = session.run(distribution_query)
        for record in results:
            entity_type = record['entity_type'] or 'Unknown'
            count = record['count']
            print(f"   {entity_type}: {count}")
        
        # Query 7: Search entities by name pattern
        print("\n7️⃣ Search Entities (containing 'tech' or 'Tech')")
        print("-" * 30)
        search_query = """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS 'tech'
        RETURN e.name, e.type, e.description
        LIMIT 10
        """
        
        results = session.run(search_query)
        for i, record in enumerate(results, 1):
            name = record['e.name'] or 'N/A'
            entity_type = record['e.type'] or 'N/A'
            description = record['e.description'] or 'N/A'
            # Truncate long descriptions
            if len(description) > 100:
                description = description[:97] + "..."
            print(f"   {i}. {name} ({entity_type})")
            print(f"      Description: {description}")
        
        # Query 8: Organizations by industry
        print("\n8️⃣ Organizations by Industry")
        print("-" * 30)
        industry_query = """
        MATCH (o:Organization)
        WHERE size(o.industry) > 0
        UNWIND o.industry as industry
        RETURN industry, count(o) as org_count
        ORDER BY org_count DESC
        LIMIT 10
        """
        
        results = session.run(industry_query)
        for record in results:
            industry = record['industry']
            count = record['org_count']
            print(f"   {industry}: {count} organizations")

def run_spatial_queries(config_file: str = "config.env"):
    """Run spatial queries on entities with geographic data"""
    
    config = Neo4jConfig(config_file)
    driver = config.get_driver()
    
    print("\n🌍 Spatial Queries")
    print("=" * 60)
    
    with driver.session(database=config.database) as session:
        
        # Query 1: Entities within distance of a point (San Francisco)
        print("\n1️⃣ Entities within 50km of San Francisco")
        print("-" * 45)
        sf_query = """
        MATCH (e:Entity)
        WHERE e.location IS NOT NULL
        AND distance(e.location, point({latitude: 37.7749, longitude: -122.4194})) <= 50000
        RETURN e.name, e.type, 
               distance(e.location, point({latitude: 37.7749, longitude: -122.4194})) / 1000 as distance_km
        ORDER BY distance_km
        LIMIT 10
        """
        
        results = session.run(sf_query)
        for i, record in enumerate(results, 1):
            name = record['e.name'] or 'N/A'
            entity_type = record['e.type'] or 'N/A'
            distance = record['distance_km']
            print(f"   {i}. {name} ({entity_type})")
            print(f"      Distance: {distance:.2f} km")
        
        # Query 2: Entities by geographic region (bounding box)
        print("\n2️⃣ Entities in New York Area (Bounding Box)")
        print("-" * 45)
        ny_query = """
        MATCH (e:Entity)
        WHERE e.location IS NOT NULL
        AND e.location.latitude >= 40.4774 AND e.location.latitude <= 40.9176
        AND e.location.longitude >= -74.2591 AND e.location.longitude <= -73.7004
        RETURN e.name, e.type, e.location.latitude as lat, e.location.longitude as lon
        LIMIT 10
        """
        
        results = session.run(ny_query)
        for i, record in enumerate(results, 1):
            name = record['e.name'] or 'N/A'
            entity_type = record['e.type'] or 'N/A'
            lat = record['lat']
            lon = record['lon']
            print(f"   {i}. {name} ({entity_type})")
            print(f"      Coordinates: {lat:.4f}, {lon:.4f}")

def run_advanced_queries(config_file: str = "config.env"):
    """Run advanced analytical queries"""
    
    config = Neo4jConfig(config_file)
    driver = config.get_driver()
    
    print("\n🧠 Advanced Analytics Queries")
    print("=" * 60)
    
    with driver.session(database=config.database) as session:
        
        # Query 1: Entity growth over time (if date fields available)
        print("\n1️⃣ Articles Published by Month")
        print("-" * 35)
        timeline_query = """
        MATCH (a:Article)
        WHERE a.published_date IS NOT NULL
        WITH a.published_date as date_str
        WHERE date_str =~ '\\d{4}-\\d{2}-\\d{2}.*'
        WITH substring(date_str, 0, 7) as month
        RETURN month, count(*) as articles
        ORDER BY month DESC
        LIMIT 12
        """
        
        results = session.run(timeline_query)
        for record in results:
            month = record['month']
            count = record['articles']
            print(f"   {month}: {count} articles")
        
        # Query 2: Top entity properties
        print("\n2️⃣ Most Common Entity Properties")
        print("-" * 35)
        props_query = """
        MATCH (e:Entity)
        UNWIND keys(e.properties) as prop_key
        WHERE prop_key <> 'id' AND prop_key <> 'type'
        RETURN prop_key, count(*) as frequency
        ORDER BY frequency DESC
        LIMIT 15
        """
        
        results = session.run(props_query)
        for record in results:
            prop = record['prop_key']
            freq = record['frequency']
            print(f"   {prop}: {freq} entities")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run sample queries on Diffbot knowledge graph data")
    parser.add_argument("--config-file", default="config.env", 
                       help="Configuration file path")
    parser.add_argument("--spatial", action="store_true",
                       help="Run spatial queries")
    parser.add_argument("--advanced", action="store_true",
                       help="Run advanced analytics queries")
    
    args = parser.parse_args()
    
    # Run basic sample queries
    run_sample_queries(args.config_file)
    
    # Run spatial queries if requested
    if args.spatial:
        run_spatial_queries(args.config_file)
    
    # Run advanced queries if requested
    if args.advanced:
        run_advanced_queries(args.config_file)
    
    print("\n✅ Sample queries completed!")
    print("\nNext steps:")
    print("- Modify queries for your specific use case")
    print("- Explore entity relationships and properties")
    print("- Build custom analytics on your Diffbot data")