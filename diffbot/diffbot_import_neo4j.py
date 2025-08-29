#!/usr/bin/env python3
"""
Diffbot Knowledge Graph to Neo4j Import Script

This script imports Diffbot Knowledge Graph data into Neo4j using the Diffbot API
to extract entities and relationships, then creates a comprehensive knowledge graph.
"""

import os
import sys
import json
import asyncio
import argparse
import logging
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
import pandas as pd

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from neo4j_config import Neo4jConfig
from diffbot_client import DiffbotClient, DiffbotQueries

logger = logging.getLogger(__name__)

class DiffbotImporter:
    """Main class for importing Diffbot data into Neo4j"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize the importer with configuration"""
        self.config = Neo4jConfig(config_file)
        self.driver = self.config.get_driver()
        self.database = self.config.get_database()
        
        # Import statistics
        self.stats = {
            'entities_created': 0,
            'relationships_created': 0,
            'properties_created': 0,
            'start_time': None,
            'end_time': None
        }
        
        print(f"🔧 Diffbot Importer Configuration:")
        print(f"  Neo4j URI: {self.config.uri}")
        print(f"  Neo4j Database: {self.config.database}")
        print(f"  Diffbot API URL: {self.config.diffbot_api_base_url}")
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
            "CREATE CONSTRAINT diffbot_entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.diffbot_id IS UNIQUE",
            "CREATE CONSTRAINT person_diffbot_id IF NOT EXISTS FOR (p:Person) REQUIRE p.diffbot_id IS UNIQUE",
            "CREATE CONSTRAINT organization_diffbot_id IF NOT EXISTS FOR (o:Organization) REQUIRE o.diffbot_id IS UNIQUE",
            "CREATE CONSTRAINT article_diffbot_id IF NOT EXISTS FOR (a:Article) REQUIRE a.diffbot_id IS UNIQUE",
            
            # Indexes for performance
            "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX person_name_idx IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX organization_name_idx IF NOT EXISTS FOR (o:Organization) ON (o.name)",
            "CREATE INDEX article_title_idx IF NOT EXISTS FOR (a:Article) ON (a.title)",
            
            # Spatial index for coordinates
            "CREATE POINT INDEX entity_location_idx IF NOT EXISTS FOR (e:Entity) ON (e.location)",
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
    
    async def import_data(self, 
                         query: str = None,
                         entity_types: List[str] = None,
                         max_results: int = 10000) -> Dict[str, Any]:
        """Import Diffbot data using search query"""
        print(f"📥 Starting Diffbot import...")
        self.stats['start_time'] = datetime.now()
        
        # Validate connection first
        if not self.validate_connection():
            raise Exception("Neo4j connection validation failed")
        
        # Create schema
        self.create_schema()
        
        # Set default query if none provided
        if not query:
            if not entity_types:
                entity_types = self.config.default_entity_types
            # Use a query that returns actual Person entities
            query = "Elon Musk"
        
        print(f"Using query: {query}")
        print(f"Entity types: {entity_types}")
        
        # Initialize Diffbot client
        print(f"🔑 Using Diffbot token: {self.config.diffbot_token[:10]}...")
        async with DiffbotClient(
            token=self.config.diffbot_token,
            base_url=self.config.diffbot_api_base_url,
            request_delay=self.config.request_delay,
            max_retries=self.config.max_retries,
            timeout=self.config.timeout,
            max_concurrent=self.config.max_concurrent_requests
        ) as client:
            
            results_processed = 0
            
            try:
                # Use async pagination to fetch data
                async for entities in client.search_entities_paginated(
                    query=query,
                    entity_types=entity_types,
                    page_size=min(self.config.batch_size, 100),
                    max_results=max_results
                ):
                    if not entities:
                        break
                    
                    print(f"📄 Processing batch of {len(entities)} entities...")
                    
                    # Process and import the batch
                    batch_stats = await self._import_batch(entities)
                    
                    # Update statistics
                    self.stats['entities_created'] += batch_stats.get('entities_created', 0)
                    self.stats['relationships_created'] += batch_stats.get('relationships_created', 0)
                    self.stats['properties_created'] += batch_stats.get('properties_created', 0)
                    
                    results_processed += len(entities)
                    print(f"✅ Processed {results_processed} total entities")
                    
            except Exception as e:
                logger.error(f"Import failed: {e}")
                raise
        
        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print(f"\n🎉 Import completed successfully!")
        print(f"📊 Import Statistics:")
        print(f"  Entities processed: {results_processed}")
        print(f"  Entities created: {self.stats['entities_created']}")
        print(f"  Relationships created: {self.stats['relationships_created']}")
        print(f"  Properties created: {self.stats['properties_created']}")
        print(f"  Duration: {duration}")
        
        return self.stats
    
    async def _import_batch(self, entities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Import a batch of entities into Neo4j"""
        if not entities:
            return {'entities_created': 0, 'relationships_created': 0, 'properties_created': 0}
        
        batch_stats = {'entities_created': 0, 'relationships_created': 0, 'properties_created': 0}
        
        # Separate entities by type for optimized processing
        people = []
        organizations = []
        articles = []
        generic_entities = []
        
        for entity in entities:
            # Check both 'type' and 'types' fields for entity classification
            entity_type = entity.get('type', '')
            entity_types = entity.get('types', [])
            
            # Determine the primary entity type
            if entity_type == 'Person' or 'Person' in entity_types:
                people.append(entity)
            elif entity_type == 'Organization' or 'Organization' in entity_types:
                organizations.append(entity)
            elif entity_type == 'Article' or 'Article' in entity_types:
                articles.append(entity)
            else:
                generic_entities.append(entity)
        
        with self.driver.session(database=self.database) as session:
            # Import each entity type
            if people:
                stats = self._import_people_batch(session, people)
                self._update_batch_stats(batch_stats, stats)
            
            if organizations:
                stats = self._import_organizations_batch(session, organizations)
                self._update_batch_stats(batch_stats, stats)
            
            if articles:
                stats = self._import_articles_batch(session, articles)
                self._update_batch_stats(batch_stats, stats)
            
            if generic_entities:
                stats = self._import_generic_batch(session, generic_entities)
                self._update_batch_stats(batch_stats, stats)
        
        return batch_stats
    
    def _import_people_batch(self, session, people: List[Dict[str, Any]]) -> Dict[str, int]:
        """Import people entities"""
        records = []
        for person in people:
            # Clean and prepare the record data
            birth_date = self._clean_date_field(person.get('birthDate', ''))
            death_date = self._clean_date_field(person.get('deathDate', ''))
            occupations = self._clean_list_field(person.get('occupations', []))
            
            record = {
                'diffbot_id': person.get('id', ''),
                'name': person.get('name', ''),
                'description': person.get('summary', ''),
                'birth_date': birth_date,
                'death_date': death_date,
                'nationality': person.get('nationality', ''),
                'occupations': occupations,
                'location': self._parse_location(person.get('location')),
                'properties': self._clean_properties(person)
            }
            records.append(record)
        
        cypher_query = """
        UNWIND $records as record
        MERGE (p:Person:Entity {diffbot_id: record.diffbot_id})
        SET p.name = record.name,
            p.type = 'Person',
            p.description = record.description,
            p.birth_date = record.birth_date,
            p.death_date = record.death_date,
            p.nationality = record.nationality,
            p.occupations = record.occupations,
            p.properties = record.properties,
            p.updated_at = datetime()
        
        // Add location if available
        FOREACH (loc IN CASE WHEN record.location IS NOT NULL THEN [record.location] ELSE [] END |
            SET p.location = point({longitude: loc.longitude, latitude: loc.latitude})
        )
        
        RETURN count(p) as entities_created
        """
        
        result = session.run(cypher_query, records=records)
        summary = result.consume()
        
        return {
            'entities_created': summary.counters.nodes_created,
            'relationships_created': summary.counters.relationships_created,
            'properties_created': summary.counters.properties_set
        }
    
    def _import_organizations_batch(self, session, organizations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Import organization entities"""
        records = []
        for org in organizations:
            record = {
                'diffbot_id': org.get('id', ''),
                'name': org.get('name', ''),
                'description': org.get('summary', ''),
                'founded_date': org.get('foundedDate', ''),
                'industry': org.get('industries', []),
                'employees': self._parse_number(org.get('nbEmployeesMax', '')),
                'revenue': org.get('revenue', ''),
                'location': self._parse_location(org.get('location')),
                'properties': org
            }
            records.append(record)
        
        cypher_query = """
        UNWIND $records as record
        MERGE (o:Organization:Entity {diffbot_id: record.diffbot_id})
        SET o.name = record.name,
            o.type = 'Organization',
            o.description = record.description,
            o.founded_date = record.founded_date,
            o.industry = record.industry,
            o.employees = record.employees,
            o.revenue = record.revenue,
            o.properties = record.properties,
            o.updated_at = datetime()
        
        // Add location if available
        FOREACH (loc IN CASE WHEN record.location IS NOT NULL THEN [record.location] ELSE [] END |
            SET o.location = point({longitude: loc.longitude, latitude: loc.latitude})
        )
        
        RETURN count(o) as entities_created
        """
        
        result = session.run(cypher_query, records=records)
        summary = result.consume()
        
        return {
            'entities_created': summary.counters.nodes_created,
            'relationships_created': summary.counters.relationships_created,
            'properties_created': summary.counters.properties_set
        }
    
    def _import_articles_batch(self, session, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """Import article entities"""
        records = []
        for article in articles:
            record = {
                'diffbot_id': article.get('id', ''),
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'text': article.get('text', ''),
                'published_date': article.get('date', ''),
                'author': article.get('author', ''),
                'site_name': article.get('siteName', ''),
                'language': article.get('language', ''),
                'properties': article
            }
            records.append(record)
        
        cypher_query = """
        UNWIND $records as record
        MERGE (a:Article:Entity {diffbot_id: record.diffbot_id})
        SET a.title = record.title,
            a.type = 'Article',
            a.url = record.url,
            a.text = record.text,
            a.published_date = record.published_date,
            a.author = record.author,
            a.site_name = record.site_name,
            a.language = record.language,
            a.properties = record.properties,
            a.updated_at = datetime()
        
        RETURN count(a) as entities_created
        """
        
        result = session.run(cypher_query, records=records)
        summary = result.consume()
        
        return {
            'entities_created': summary.counters.nodes_created,
            'relationships_created': summary.counters.relationships_created,
            'properties_created': summary.counters.properties_set
        }
    
    def _import_generic_batch(self, session, entities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Import generic entities"""
        records = []
        for entity in entities:
            record = {
                'diffbot_id': entity.get('id', ''),
                'name': entity.get('name', entity.get('title', '')),
                'type': entity.get('type', 'Entity'),
                'description': entity.get('summary', entity.get('description', '')),
                'properties': entity
            }
            records.append(record)
        
        cypher_query = """
        UNWIND $records as record
        MERGE (e:Entity {diffbot_id: record.diffbot_id})
        SET e.name = record.name,
            e.type = record.type,
            e.description = record.description,
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
    
    def _parse_location(self, location_data: Any) -> Optional[Dict[str, float]]:
        """Parse location data to coordinates"""
        if not location_data:
            return None
        
        try:
            if isinstance(location_data, dict):
                lat = location_data.get('latitude', location_data.get('lat'))
                lon = location_data.get('longitude', location_data.get('lon', location_data.get('lng')))
                
                if lat is not None and lon is not None:
                    return {'latitude': float(lat), 'longitude': float(lon)}
            
            return None
        except (ValueError, TypeError):
            logger.warning(f"Failed to parse location: {location_data}")
            return None
    
    def _parse_number(self, num_str: Any) -> Optional[int]:
        """Parse number from various formats"""
        if not num_str:
            return None
        
        try:
            return int(float(str(num_str)))
        except (ValueError, TypeError):
            return None
    
    def _clean_date_field(self, date_field: Any) -> Optional[str]:
        """Clean date fields that might be complex objects"""
        if not date_field:
            return None
        
        try:
            if isinstance(date_field, dict):
                # Extract the string value from complex date objects
                if 'str' in date_field:
                    return str(date_field['str'])
                elif 'value' in date_field:
                    return str(date_field['value'])
                else:
                    # Try to find any string value in the dict
                    for key, value in date_field.items():
                        if isinstance(value, str):
                            return value
                    return None
            elif isinstance(date_field, str):
                return date_field
            else:
                return str(date_field)
        except Exception:
            return None
    
    def _clean_list_field(self, list_field: Any) -> List[str]:
        """Clean list fields to ensure they contain only strings"""
        if not list_field:
            return []
        
        try:
            if isinstance(list_field, list):
                cleaned = []
                for item in list_field:
                    if isinstance(item, str):
                        cleaned.append(item)
                    elif isinstance(item, dict) and 'name' in item:
                        cleaned.append(str(item['name']))
                    else:
                        cleaned.append(str(item))
                return cleaned
            else:
                return [str(list_field)]
        except Exception:
            return []
    
    def _clean_properties(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Clean entity properties to ensure they're Neo4j compatible"""
        cleaned = {}
        for key, value in entity.items():
            try:
                if isinstance(value, (str, int, float, bool)) or value is None:
                    cleaned[key] = value
                elif isinstance(value, list):
                    cleaned[key] = self._clean_list_field(value)
                elif isinstance(value, dict):
                    # For complex objects, try to extract meaningful string values
                    if 'name' in value:
                        cleaned[key] = str(value['name'])
                    elif 'str' in value:
                        cleaned[key] = str(value['str'])
                    else:
                        cleaned[key] = str(value)
                else:
                    cleaned[key] = str(value)
            except Exception:
                # If we can't clean a field, skip it
                continue
        
        return cleaned
    
    def _update_batch_stats(self, batch_stats: Dict[str, int], new_stats: Dict[str, int]):
        """Update batch statistics"""
        for key in batch_stats:
            batch_stats[key] += new_stats.get(key, 0)
    
    def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            self.driver.close()

async def main():
    """Main function to run the Diffbot importer"""
    parser = argparse.ArgumentParser(description="Import Diffbot Knowledge Graph data into Neo4j")
    parser.add_argument("--config-file", default="config.env", 
                       help="Configuration file path")
    parser.add_argument("--query", 
                       help="Diffbot search query (e.g., 'type:Organization name:\"OpenAI\"')")
    parser.add_argument("--entity-types", nargs='+', 
                       help="Entity types to import (Person, Organization, Article)")
    parser.add_argument("--max-results", type=int, default=10000,
                       help="Maximum number of results to import")
    
    args = parser.parse_args()
    
    # Initialize and run importer
    importer = DiffbotImporter(args.config_file)
    
    try:
        stats = await importer.import_data(
            query=args.query,
            entity_types=args.entity_types,
            max_results=args.max_results
        )
        print(f"✅ Import completed successfully: {stats}")
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        sys.exit(1)
        
    finally:
        importer.close()

if __name__ == "__main__":
    asyncio.run(main())