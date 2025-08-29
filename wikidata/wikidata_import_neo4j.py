#!/usr/bin/env python3
"""
Wikidata to Neo4j Import Script

This script imports Wikidata knowledge graph data into Neo4j using SPARQL queries
to extract entities and relationships, then creates a comprehensive knowledge graph.
"""

import os
import sys
import json
import uuid
import argparse
import logging
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
import pandas as pd
from urllib.parse import urlparse

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from neo4j_config import Neo4jConfig
from wikidata_sparql import WikidataSPARQLClient, WikidataQueries

logger = logging.getLogger(__name__)

class WikidataImporter:
    """Main class for importing Wikidata into Neo4j"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize the importer with configuration"""
        self.config = Neo4jConfig(config_file)
        self.driver = self.config.get_driver()
        self.database = self.config.get_database()
        
        # Initialize SPARQL client
        self.sparql_client = WikidataSPARQLClient(
            endpoint=self.config.wikidata_endpoint,
            request_delay=self.config.request_delay,
            max_retries=self.config.max_retries,
            timeout=self.config.timeout
        )
        
        # Import statistics
        self.stats = {
            'entities_created': 0,
            'relationships_created': 0,
            'properties_created': 0,
            'start_time': None,
            'end_time': None
        }
        
        print(f"🔧 Wikidata Importer Configuration:")
        print(f"  Neo4j URI: {self.config.uri}")
        print(f"  Neo4j Database: {self.config.database}")
        print(f"  Wikidata Endpoint: {self.config.wikidata_endpoint}")
        print(f"  Batch Size: {self.config.batch_size}")
        print(f"  Request Delay: {self.config.request_delay}s")
    
    def validate_connection(self) -> bool:
        """Validate Neo4j connection"""
        try:
            if not self.config.validate_connection():
                logger.error("❌ Neo4j connection validation failed")
                return False
            print("✅ Neo4j connection validated")
            return True
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def create_schema(self):
        """Create Neo4j schema constraints and indexes"""
        print("🏗️ Creating Neo4j schema...")
        
        constraints_and_indexes = [
            # Constraints for unique properties
            "CREATE CONSTRAINT wikidata_entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.wikidata_id IS UNIQUE",
            "CREATE CONSTRAINT person_wikidata_id IF NOT EXISTS FOR (p:Person) REQUIRE p.wikidata_id IS UNIQUE", 
            "CREATE CONSTRAINT place_wikidata_id IF NOT EXISTS FOR (p:Place) REQUIRE p.wikidata_id IS UNIQUE",
            "CREATE CONSTRAINT organization_wikidata_id IF NOT EXISTS FOR (o:Organization) REQUIRE o.wikidata_id IS UNIQUE",
            
            # Indexes for performance
            "CREATE INDEX entity_label_idx IF NOT EXISTS FOR (e:Entity) ON (e.label)",
            "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX person_name_idx IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX place_name_idx IF NOT EXISTS FOR (p:Place) ON (p.name)",
            "CREATE INDEX organization_name_idx IF NOT EXISTS FOR (o:Organization) ON (o.name)",
            
            # Spatial index for coordinates
            "CREATE POINT INDEX place_coordinates_idx IF NOT EXISTS FOR (p:Place) ON (p.coordinates)",
        ]
        
        with self.driver.session(database=self.database) as session:
            for statement in constraints_and_indexes:
                try:
                    session.run(statement)
                    logger.debug(f"Executed: {statement}")
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        logger.warning(f"Schema statement failed: {statement} - {e}")
        
        print("✅ Schema created successfully")
    
    def import_data(self, 
                   query_type: str = "scientists",
                   limit: int = 1000,
                   sparql_query: Optional[str] = None) -> Dict[str, Any]:
        """Import Wikidata using specified query type or custom SPARQL"""
        print(f"📥 Starting Wikidata import ({query_type})...")
        self.stats['start_time'] = datetime.now()
        
        # Validate connection first
        if not self.validate_connection():
            raise Exception("Neo4j connection validation failed")
        
        # Create schema
        self.create_schema()
        
        # Get SPARQL query based on type
        if sparql_query:
            query = sparql_query
            print(f"Using custom SPARQL query (length: {len(query)})")
        else:
            query = self._get_predefined_query(query_type, limit)
            print(f"Using predefined query type: {query_type}")
        
        # Execute query and process results
        results_processed = 0
        
        try:
            # Use pagination for large datasets
            page_size = min(self.config.batch_size, 5000)  # SPARQL endpoint limits
            
            for page_num, results in enumerate(self.sparql_client.execute_query_paginated(
                query, page_size=page_size, max_results=limit
            ), 1):
                if not results:
                    break
                    
                print(f"📄 Processing page {page_num} ({len(results)} results)...")
                
                # Convert to DataFrame for easier processing
                df = self.sparql_client._bindings_to_dataframe(results)
                
                # Process and import the batch
                batch_stats = self._import_batch(df, query_type)
                
                # Update statistics
                self.stats['entities_created'] += batch_stats.get('entities_created', 0)
                self.stats['relationships_created'] += batch_stats.get('relationships_created', 0)
                self.stats['properties_created'] += batch_stats.get('properties_created', 0)
                
                results_processed += len(results)
                
                print(f"✅ Processed {results_processed} total results")
                
        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise
        
        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print(f"\n🎉 Import completed successfully!")
        print(f"📊 Import Statistics:")
        print(f"  Results processed: {results_processed}")
        print(f"  Entities created: {self.stats['entities_created']}")
        print(f"  Relationships created: {self.stats['relationships_created']}")
        print(f"  Properties created: {self.stats['properties_created']}")
        print(f"  Duration: {duration}")
        
        return self.stats
    
    def _get_predefined_query(self, query_type: str, limit: int) -> str:
        """Get predefined SPARQL query by type"""
        queries = {
            'scientists': WikidataQueries.get_scientists(limit),
            'cities': WikidataQueries.get_cities(limit=limit),
            'universities': WikidataQueries.get_universities(limit),
            'companies': WikidataQueries.get_companies(limit)
        }
        
        if query_type not in queries:
            available = ', '.join(queries.keys())
            raise ValueError(f"Unknown query type '{query_type}'. Available: {available}")
        
        return queries[query_type]
    
    def _import_batch(self, df: pd.DataFrame, query_type: str) -> Dict[str, int]:
        """Import a batch of results into Neo4j"""
        if df.empty:
            return {'entities_created': 0, 'relationships_created': 0, 'properties_created': 0}
        
        batch_stats = {'entities_created': 0, 'relationships_created': 0, 'properties_created': 0}
        
        with self.driver.session(database=self.database) as session:
            # Process based on query type
            if query_type == "scientists":
                batch_stats = self._import_scientists_batch(session, df)
            elif query_type == "cities":
                batch_stats = self._import_cities_batch(session, df)
            elif query_type == "universities":
                batch_stats = self._import_universities_batch(session, df)
            elif query_type == "companies":
                batch_stats = self._import_companies_batch(session, df)
            else:
                # Generic import for custom queries
                batch_stats = self._import_generic_batch(session, df)
        
        return batch_stats
    
    def _import_scientists_batch(self, session, df: pd.DataFrame) -> Dict[str, int]:
        """Import scientists batch with relationships"""
        entities_created = 0
        relationships_created = 0
        
        # Convert DataFrame to records for batch processing
        records = []
        for _, row in df.iterrows():
            wikidata_id = self._extract_wikidata_id(row.get('item', ''))
            if not wikidata_id:
                continue
                
            record = {
                'wikidata_id': wikidata_id,
                'name': row.get('itemLabel', ''),
                'birth_date': row.get('birthDate', ''),
                'death_date': row.get('deathDate', ''),
                'field': row.get('fieldLabel', ''),
                'country': row.get('countryLabel', ''),
                'coordinates': self._parse_coordinates(row.get('coordinates', ''))
            }
            records.append(record)
        
        if not records:
            return {'entities_created': 0, 'relationships_created': 0, 'properties_created': 0}
        
        # Batch create scientists
        cypher_query = """
        UNWIND $records as record
        MERGE (p:Person:Entity {wikidata_id: record.wikidata_id})
        SET p.name = record.name,
            p.label = record.name,
            p.type = 'Person',
            p.occupation = 'Scientist',
            p.birth_date = record.birth_date,
            p.death_date = record.death_date,
            p.updated_at = datetime()
        
        // Add coordinates if available
        FOREACH (coord IN CASE WHEN record.coordinates IS NOT NULL THEN [record.coordinates] ELSE [] END |
            SET p.coordinates = point({longitude: coord.longitude, latitude: coord.latitude})
        )
        
        // Create field relationship if available
        FOREACH (field_name IN CASE WHEN record.field <> '' THEN [record.field] ELSE [] END |
            MERGE (f:Field:Entity {wikidata_id: 'FIELD_' + replace(field_name, ' ', '_')})
            SET f.name = field_name,
                f.label = field_name,
                f.type = 'Field',
                f.updated_at = datetime()
            MERGE (p)-[:WORKS_IN]->(f)
        )
        
        // Create country relationship if available  
        FOREACH (country_name IN CASE WHEN record.country <> '' THEN [record.country] ELSE [] END |
            MERGE (c:Country:Entity {wikidata_id: 'COUNTRY_' + replace(country_name, ' ', '_')})
            SET c.name = country_name,
                c.label = country_name,
                c.type = 'Country',
                c.updated_at = datetime()
            MERGE (p)-[:CITIZEN_OF]->(c)
        )
        
        RETURN count(p) as entities_created
        """
        
        result = session.run(cypher_query, records=records)
        summary = result.consume()
        
        entities_created = summary.counters.nodes_created
        relationships_created = summary.counters.relationships_created
        
        return {
            'entities_created': entities_created,
            'relationships_created': relationships_created,
            'properties_created': summary.counters.properties_set
        }
    
    def _import_cities_batch(self, session, df: pd.DataFrame) -> Dict[str, int]:
        """Import cities batch with relationships"""
        records = []
        for _, row in df.iterrows():
            wikidata_id = self._extract_wikidata_id(row.get('item', ''))
            if not wikidata_id:
                continue
                
            record = {
                'wikidata_id': wikidata_id,
                'name': row.get('itemLabel', ''),
                'population': self._parse_number(row.get('population', '')),
                'state': row.get('stateLabel', ''),
                'mayor': row.get('mayorLabel', ''),
                'coordinates': self._parse_coordinates(row.get('coordinates', ''))
            }
            records.append(record)
        
        if not records:
            return {'entities_created': 0, 'relationships_created': 0, 'properties_created': 0}
        
        cypher_query = """
        UNWIND $records as record
        MERGE (c:City:Place:Entity {wikidata_id: record.wikidata_id})
        SET c.name = record.name,
            c.label = record.name,
            c.type = 'City',
            c.population = record.population,
            c.updated_at = datetime()
        
        // Add coordinates if available
        FOREACH (coord IN CASE WHEN record.coordinates IS NOT NULL THEN [record.coordinates] ELSE [] END |
            SET c.coordinates = point({longitude: coord.longitude, latitude: coord.latitude})
        )
        
        // Create state relationship if available
        FOREACH (state_name IN CASE WHEN record.state <> '' THEN [record.state] ELSE [] END |
            MERGE (s:State:Place:Entity {wikidata_id: 'STATE_' + replace(state_name, ' ', '_')})
            SET s.name = state_name,
                s.label = state_name,
                s.type = 'State',
                s.updated_at = datetime()
            MERGE (c)-[:LOCATED_IN]->(s)
        )
        
        // Create mayor relationship if available
        FOREACH (mayor_name IN CASE WHEN record.mayor <> '' THEN [record.mayor] ELSE [] END |
            MERGE (m:Person:Entity {wikidata_id: 'MAYOR_' + replace(mayor_name, ' ', '_')})
            SET m.name = mayor_name,
                m.label = mayor_name,
                m.type = 'Person',
                m.updated_at = datetime()
            MERGE (m)-[:MAYOR_OF]->(c)
        )
        
        RETURN count(c) as entities_created
        """
        
        result = session.run(cypher_query, records=records)
        summary = result.consume()
        
        return {
            'entities_created': summary.counters.nodes_created,
            'relationships_created': summary.counters.relationships_created,
            'properties_created': summary.counters.properties_set
        }
    
    def _import_universities_batch(self, session, df: pd.DataFrame) -> Dict[str, int]:
        """Import universities batch with relationships"""
        records = []
        for _, row in df.iterrows():
            wikidata_id = self._extract_wikidata_id(row.get('item', ''))
            if not wikidata_id:
                continue
                
            record = {
                'wikidata_id': wikidata_id,
                'name': row.get('itemLabel', ''),
                'country': row.get('countryLabel', ''),
                'founded': row.get('founded', ''),
                'students_count': self._parse_number(row.get('studentsCount', '')),
                'coordinates': self._parse_coordinates(row.get('coordinates', ''))
            }
            records.append(record)
        
        if not records:
            return {'entities_created': 0, 'relationships_created': 0, 'properties_created': 0}
        
        cypher_query = """
        UNWIND $records as record
        MERGE (u:University:Organization:Entity {wikidata_id: record.wikidata_id})
        SET u.name = record.name,
            u.label = record.name,
            u.type = 'University',
            u.founded = record.founded,
            u.students_count = record.students_count,
            u.updated_at = datetime()
        
        // Add coordinates if available
        FOREACH (coord IN CASE WHEN record.coordinates IS NOT NULL THEN [record.coordinates] ELSE [] END |
            SET u.coordinates = point({longitude: coord.longitude, latitude: coord.latitude})
        )
        
        // Create country relationship if available
        FOREACH (country_name IN CASE WHEN record.country <> '' THEN [record.country] ELSE [] END |
            MERGE (country:Country:Entity {wikidata_id: 'COUNTRY_' + replace(country_name, ' ', '_')})
            SET country.name = country_name,
                country.label = country_name,
                country.type = 'Country',
                country.updated_at = datetime()
            MERGE (u)-[:LOCATED_IN]->(country)
        )
        
        RETURN count(u) as entities_created
        """
        
        result = session.run(cypher_query, records=records)
        summary = result.consume()
        
        return {
            'entities_created': summary.counters.nodes_created,
            'relationships_created': summary.counters.relationships_created,
            'properties_created': summary.counters.properties_set
        }
    
    def _import_companies_batch(self, session, df: pd.DataFrame) -> Dict[str, int]:
        """Import companies batch with relationships"""
        records = []
        for _, row in df.iterrows():
            wikidata_id = self._extract_wikidata_id(row.get('item', ''))
            if not wikidata_id:
                continue
                
            record = {
                'wikidata_id': wikidata_id,
                'name': row.get('itemLabel', ''),
                'country': row.get('countryLabel', ''),
                'founded': row.get('founded', ''),
                'ceo': row.get('ceo', ''),
                'industry': row.get('industry', ''),
                'coordinates': self._parse_coordinates(row.get('coordinates', ''))
            }
            records.append(record)
        
        if not records:
            return {'entities_created': 0, 'relationships_created': 0, 'properties_created': 0}
        
        cypher_query = """
        UNWIND $records as record
        MERGE (c:Company:Organization:Entity {wikidata_id: record.wikidata_id})
        SET c.name = record.name,
            c.label = record.name,
            c.type = 'Company',
            c.founded = record.founded,
            c.updated_at = datetime()
        
        // Add coordinates if available
        FOREACH (coord IN CASE WHEN record.coordinates IS NOT NULL THEN [record.coordinates] ELSE [] END |
            SET c.coordinates = point({longitude: coord.longitude, latitude: coord.latitude})
        )
        
        // Create country relationship if available
        FOREACH (country_name IN CASE WHEN record.country <> '' THEN [record.country] ELSE [] END |
            MERGE (country:Country:Entity {wikidata_id: 'COUNTRY_' + replace(country_name, ' ', '_')})
            SET country.name = country_name,
                country.label = country_name,
                country.type = 'Country',
                country.updated_at = datetime()
            MERGE (c)-[:LOCATED_IN]->(country)
        )
        
        RETURN count(c) as entities_created
        """
        
        result = session.run(cypher_query, records=records)
        summary = result.consume()
        
        return {
            'entities_created': summary.counters.nodes_created,
            'relationships_created': summary.counters.relationships_created,
            'properties_created': summary.counters.properties_set
        }
    
    def _import_generic_batch(self, session, df: pd.DataFrame) -> Dict[str, int]:
        """Generic import for custom queries"""
        # This would handle arbitrary SPARQL results
        # For now, create basic entities
        records = []
        for _, row in df.iterrows():
            wikidata_id = self._extract_wikidata_id(row.get('item', ''))
            if not wikidata_id:
                continue
                
            record = {
                'wikidata_id': wikidata_id,
                'name': row.get('itemLabel', ''),
                'description': row.get('itemDescription', ''),
                'properties': {k: v for k, v in row.to_dict().items() 
                             if k not in ['item', 'itemLabel', 'itemDescription']}
            }
            records.append(record)
        
        if not records:
            return {'entities_created': 0, 'relationships_created': 0, 'properties_created': 0}
        
        cypher_query = """
        UNWIND $records as record
        MERGE (e:Entity {wikidata_id: record.wikidata_id})
        SET e.name = record.name,
            e.label = record.name,
            e.description = record.description,
            e.type = 'Entity',
            e.properties = record.properties,
            e.updated_at = datetime()
        
        RETURN count(e) as entities_created
        """
        
        result = session.run(cypher_query, records=records)
        summary = result.consume()
        
        return {
            'entities_created': summary.counters.nodes_created,
            'relationships_created': summary.counters.relationships_created,
            'properties_created': summary.counters.properties_set
        }
    
    def _extract_wikidata_id(self, uri: str) -> Optional[str]:
        """Extract Wikidata ID from URI"""
        if not uri:
            return None
        
        # Handle full URIs like http://www.wikidata.org/entity/Q42
        if uri.startswith('http'):
            return uri.split('/')[-1]
        
        # Handle direct IDs like Q42
        if uri.startswith('Q') or uri.startswith('P'):
            return uri
        
        return None
    
    def _parse_coordinates(self, coord_str: str) -> Optional[Dict[str, float]]:
        """Parse coordinate string to point format"""
        if not coord_str or coord_str == '':
            return None
        
        try:
            # Handle WKT Point format: "Point(-122.4194 37.7749)"
            if coord_str.startswith('Point('):
                coords = coord_str.replace('Point(', '').replace(')', '')
                lon, lat = map(float, coords.split())
                return {'longitude': lon, 'latitude': lat}
            
            # Handle other coordinate formats as needed
            return None
            
        except (ValueError, IndexError):
            logger.warning(f"Failed to parse coordinates: {coord_str}")
            return None
    
    def _parse_number(self, num_str: str) -> Optional[int]:
        """Parse number string to integer"""
        if not num_str or num_str == '':
            return None
            
        try:
            return int(float(num_str))
        except (ValueError, TypeError):
            return None
    
    def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            self.driver.close()

def main():
    """Main function to run the Wikidata importer"""
    parser = argparse.ArgumentParser(description="Import Wikidata into Neo4j")
    parser.add_argument("--config-file", default="config.env", 
                       help="Configuration file path")
    parser.add_argument("--query-type", default="scientists",
                       choices=["scientists", "cities", "universities", "companies", "custom"],
                       help="Type of predefined query to run")
    parser.add_argument("--limit", type=int, default=1000,
                       help="Maximum number of results to import")
    parser.add_argument("--sparql-file", help="Path to custom SPARQL query file")
    parser.add_argument("--sparql-query", help="Custom SPARQL query string")
    
    args = parser.parse_args()
    
    # Load custom SPARQL query if provided
    custom_query = None
    if args.sparql_file:
        with open(args.sparql_file, 'r') as f:
            custom_query = f.read()
    elif args.sparql_query:
        custom_query = args.sparql_query
    
    # Initialize and run importer
    importer = WikidataImporter(args.config_file)
    
    try:
        stats = importer.import_data(
            query_type=args.query_type,
            limit=args.limit,
            sparql_query=custom_query
        )
        print(f"✅ Import completed successfully: {stats}")
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        sys.exit(1)
        
    finally:
        importer.close()

if __name__ == "__main__":
    main()