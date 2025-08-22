#!/usr/bin/env python3
"""
Simple test script to verify Neo4j connection
"""

from neo4j import GraphDatabase
from neo4j_config import Neo4jConfig

def main():
    print("🔧 Testing Neo4j Connection...")
    
    driver = None
    try:
        # Load configuration
        config = Neo4jConfig()
        config.print_config()
        
        # Create Neo4j driver
        driver = GraphDatabase.driver(
            config.uri,
            auth=config.get_auth(),
            **config.get_driver_config()
        )
        print("✅ Neo4j driver created successfully")
        
        # Test with a simple query
        with driver.session(database=config.database) as session:
            result = session.run("RETURN 1 as test, datetime() as current_time")
            record = result.single()
            print("✅ Query executed successfully")
            print(f"Test value: {record['test']}")
            print(f"Current time: {record['current_time']}")
            
        # Test database info
        with driver.session(database=config.database) as session:
            result = session.run("CALL dbms.components() YIELD name, versions")
            for record in result:
                print(f"Component: {record['name']}, Versions: {record['versions']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        if driver:
            driver.close()

if __name__ == "__main__":
    main()