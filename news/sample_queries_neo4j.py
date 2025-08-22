#!/usr/bin/env python3
"""
Sample Cypher Queries for News Knowledge Graph

This script demonstrates various query patterns for the news knowledge graph in Neo4j,
including basic queries, filtering, relationships, and vector similarity search.
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from neo4j_config import load_neo4j_config
from vector_search_neo4j import NewsVectorSearchNeo4j

# Load environment variables
load_dotenv()

class NewsQueryExamplesNeo4j:
    """Class containing example Cypher queries for the news knowledge graph"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize the query examples"""
        self.config = load_neo4j_config(config_file)
        self.driver = self.config.get_driver()
        self.database = self.config.get_database()
        
        try:
            self.vector_search = NewsVectorSearchNeo4j(config_file)
        except:
            self.vector_search = None
            print("⚠️  Vector search not available")
        
        print(f"🔧 Configuration loaded for Neo4j query examples")
    
    def run_basic_queries(self):
        """Run basic queries to explore the knowledge graph"""
        print("\n" + "="*60)
        print("📚 BASIC CYPHER QUERIES")
        print("="*60)
        
        # Query 1: Get all articles
        print("\n1. Getting all articles...")
        query1 = """
        MATCH (a:Article) 
        RETURN a.uri, a.title, a.abstract, a.published 
        LIMIT 5
        """
        self._execute_query(query1, "Basic articles query")
        
        # Query 2: Get all topics with article counts
        print("\n2. Getting all topics...")
        query2 = """
        MATCH (t:Topic)<-[:HAS_TOPIC]-(a:Article)
        RETURN t.name as topic, count(a) as article_count
        ORDER BY article_count DESC
        LIMIT 10
        """
        self._execute_query(query2, "Topics with article counts")
        
        # Query 3: Get all organizations with article counts
        print("\n3. Getting all organizations...")
        query3 = """
        MATCH (o:Organization)<-[:MENTIONS_ORGANIZATION]-(a:Article)
        RETURN o.name as organization, count(a) as article_count
        ORDER BY article_count DESC
        LIMIT 10
        """
        self._execute_query(query3, "Organizations with article counts")
    
    def run_filtering_queries(self):
        """Run queries with filtering"""
        print("\n" + "="*60)
        print("🔍 FILTERING QUERIES")
        print("="*60)
        
        # Query 1: Articles with abstracts
        print("\n1. Articles with abstracts...")
        query1 = """
        MATCH (a:Article) 
        WHERE a.abstract IS NOT NULL AND a.abstract <> ""
        RETURN a.uri, a.title, a.abstract 
        LIMIT 5
        """
        self._execute_query(query1, "Articles with abstracts")
        
        # Query 2: Articles with embeddings
        print("\n2. Articles with embeddings...")
        query2 = """
        MATCH (a:Article) 
        WHERE a.embedding IS NOT NULL
        RETURN a.uri, a.title, a.abstract 
        LIMIT 5
        """
        self._execute_query(query2, "Articles with embeddings")
        
        # Query 3: Articles with topics
        print("\n3. Articles with topics...")
        query3 = """
        MATCH (a:Article)-[:HAS_TOPIC]->(t:Topic)
        RETURN a.uri, a.title, collect(t.name) as topics 
        LIMIT 5
        """
        self._execute_query(query3, "Articles with topics")
    
    def run_relationship_queries(self):
        """Run queries exploring relationships"""
        print("\n" + "="*60)
        print("🔗 RELATIONSHIP QUERIES")
        print("="*60)
        
        # Query 1: Articles with all related entities
        print("\n1. Articles with all related entities...")
        query1 = """
        MATCH (a:Article)
        OPTIONAL MATCH (a)-[:HAS_TOPIC]->(t:Topic)
        OPTIONAL MATCH (a)-[:MENTIONS_ORGANIZATION]->(o:Organization)
        OPTIONAL MATCH (a)-[:MENTIONS_PERSON]->(p:Person)
        OPTIONAL MATCH (a)-[:LOCATED_IN]->(g:Geo)
        OPTIONAL MATCH (a)-[:WRITTEN_BY]->(au:Author)
        RETURN a.uri, a.title, a.abstract,
               collect(DISTINCT t.name) as topics,
               collect(DISTINCT o.name) as organizations,
               collect(DISTINCT p.name) as persons,
               collect(DISTINCT g.name) as locations,
               collect(DISTINCT au.name) as authors
        LIMIT 3
        """
        self._execute_query(query1, "Articles with all relationships")
        
        # Query 2: Topics with their articles
        print("\n2. Topics with their articles...")
        query2 = """
        MATCH (t:Topic)<-[:HAS_TOPIC]-(a:Article)
        RETURN t.name as topic, 
               collect({title: a.title, published: a.published}) as articles
        ORDER BY size(articles) DESC
        LIMIT 5
        """
        self._execute_query(query2, "Topics with articles")
        
        # Query 3: Organizations with their articles
        print("\n3. Organizations with their articles...")
        query3 = """
        MATCH (o:Organization)<-[:MENTIONS_ORGANIZATION]-(a:Article)
        RETURN o.name as organization, 
               collect({title: a.title, published: a.published}) as articles
        ORDER BY size(articles) DESC
        LIMIT 5
        """
        self._execute_query(query3, "Organizations with articles")
    
    def run_text_search_queries(self):
        """Run text search queries"""
        print("\n" + "="*60)
        print("🔤 FULLTEXT SEARCH QUERIES")
        print("="*60)
        
        # Query 1: Full-text search in articles
        print("\n1. Full-text search for 'technology AI'...")
        query1 = """
        CALL db.index.fulltext.queryNodes('article_text', 'technology AI') 
        YIELD node, score
        RETURN node.uri, node.title, node.abstract, score
        LIMIT 5
        """
        self._execute_query(query1, "Full-text search for 'technology AI'")
        
        # Query 2: Search articles by title contains
        print("\n2. Search articles with 'climate' in title...")
        query2 = """
        MATCH (a:Article) 
        WHERE a.title CONTAINS 'climate' OR a.title CONTAINS 'Climate'
        RETURN a.uri, a.title, a.abstract
        LIMIT 5
        """
        self._execute_query(query2, "Articles with 'climate' in title")
        
        # Query 3: Search topics by name
        print("\n3. Search topics containing 'politics'...")
        query3 = """
        MATCH (t:Topic)<-[:HAS_TOPIC]-(a:Article)
        WHERE toLower(t.name) CONTAINS 'politics'
        RETURN t.name as topic, 
               collect(a.title) as article_titles
        LIMIT 5
        """
        self._execute_query(query3, "Search topics for 'politics'")
    
    def run_aggregation_queries(self):
        """Run aggregation queries"""
        print("\n" + "="*60)
        print("📊 AGGREGATION QUERIES")
        print("="*60)
        
        # Query 1: Count articles by topic
        print("\n1. Count articles by topic...")
        query1 = """
        MATCH (t:Topic)<-[:HAS_TOPIC]-(a:Article)
        RETURN t.name as topic, count(a) as article_count
        ORDER BY article_count DESC
        LIMIT 10
        """
        self._execute_query(query1, "Article count by topic")
        
        # Query 2: Count articles by organization
        print("\n2. Count articles by organization...")
        query2 = """
        MATCH (o:Organization)<-[:MENTIONS_ORGANIZATION]-(a:Article)
        RETURN o.name as organization, count(a) as article_count
        ORDER BY article_count DESC
        LIMIT 10
        """
        self._execute_query(query2, "Article count by organization")
        
        # Query 3: Count articles by author
        print("\n3. Count articles by author...")
        query3 = """
        MATCH (au:Author)<-[:WRITTEN_BY]-(a:Article)
        RETURN au.name as author, count(a) as article_count
        ORDER BY article_count DESC
        LIMIT 10
        """
        self._execute_query(query3, "Article count by author")
    
    def run_geospatial_queries(self):
        """Run geospatial queries"""
        print("\n" + "="*60)
        print("🌍 GEOSPATIAL QUERIES")
        print("="*60)
        
        # Query 1: Articles with geolocation
        print("\n1. Articles with geographic locations...")
        query1 = """
        MATCH (a:Article)-[:LOCATED_IN]->(g:Geo)
        WHERE g.location IS NOT NULL
        RETURN a.title, g.name, 
               g.location.latitude as latitude, 
               g.location.longitude as longitude
        LIMIT 5
        """
        self._execute_query(query1, "Articles with coordinates")
        
        # Query 2: Find articles near a specific location (example: New York City)
        print("\n2. Articles near New York City (within 100km)...")
        query2 = """
        MATCH (a:Article)-[:LOCATED_IN]->(g:Geo)
        WHERE g.location IS NOT NULL
        WITH a, g, distance(g.location, point({latitude: 40.7128, longitude: -74.0060})) as dist
        WHERE dist < 100000  // 100km in meters
        RETURN a.title, g.name, round(dist/1000) as distance_km
        ORDER BY dist
        LIMIT 5
        """
        self._execute_query(query2, "Articles near NYC")
    
    def run_temporal_queries(self):
        """Run temporal queries"""
        print("\n" + "="*60)
        print("📅 TEMPORAL QUERIES")
        print("="*60)
        
        # Query 1: Articles by publication year
        print("\n1. Articles by publication year...")
        query1 = """
        MATCH (a:Article)
        WHERE a.published IS NOT NULL
        RETURN date(a.published).year as year, count(a) as article_count
        ORDER BY year DESC
        LIMIT 10
        """
        self._execute_query(query1, "Articles by year")
        
        # Query 2: Recent articles (last 30 days from a specific date)
        print("\n2. Recent articles...")
        query2 = """
        MATCH (a:Article)
        WHERE a.published IS NOT NULL 
        AND a.published >= datetime() - duration({days: 30})
        RETURN a.title, a.published
        ORDER BY a.published DESC
        LIMIT 5
        """
        self._execute_query(query2, "Recent articles")
    
    def run_vector_search_examples(self):
        """Run vector similarity search examples"""
        print("\n" + "="*60)
        print("🧠 VECTOR SIMILARITY SEARCH")
        print("="*60)
        
        if not self.vector_search:
            print("⚠️  Vector search not available")
            return
        
        # Example 1: Search for technology articles
        print("\n1. Searching for technology articles...")
        try:
            results = self.vector_search.search("artificial intelligence and machine learning", limit=3)
            if results:
                print(f"✅ Found {len(results)} technology articles")
                for i, article in enumerate(results, 1):
                    print(f"   {i}. {article.get('title', 'No title')} (score: {article.get('score', 'N/A')})")
            else:
                print("⚠️  No technology articles found")
        except Exception as e:
            print(f"❌ Vector search failed: {e}")
        
        # Example 2: Search for climate change articles
        print("\n2. Searching for climate change articles...")
        try:
            results = self.vector_search.search("climate change and global warming", limit=3)
            if results:
                print(f"✅ Found {len(results)} climate change articles")
                for i, article in enumerate(results, 1):
                    print(f"   {i}. {article.get('title', 'No title')} (score: {article.get('score', 'N/A')})")
            else:
                print("⚠️  No climate change articles found")
        except Exception as e:
            print(f"❌ Vector search failed: {e}")
        
        # Example 3: Search for political articles
        print("\n3. Searching for political articles...")
        try:
            results = self.vector_search.search("politics and government", limit=3)
            if results:
                print(f"✅ Found {len(results)} political articles")
                for i, article in enumerate(results, 1):
                    print(f"   {i}. {article.get('title', 'No title')} (score: {article.get('score', 'N/A')})")
            else:
                print("⚠️  No political articles found")
        except Exception as e:
            print(f"❌ Vector search failed: {e}")
    
    def _execute_query(self, query: str, description: str):
        """Execute a Cypher query and display results"""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query)
                records = list(result)
                
                print(f"✅ {description}")
                self._display_results(records)
                
        except Exception as e:
            print(f"❌ Query failed: {e}")
    
    def _display_results(self, records):
        """Display query results in a formatted way"""
        if not records:
            print("   No results found")
            return
        
        print(f"   Found {len(records)} results:")
        
        for i, record in enumerate(records[:3], 1):  # Show first 3 results
            record_dict = dict(record)
            
            # Try to display meaningful information
            if 'title' in record_dict:
                print(f"     {i}. {record_dict['title']}")
            elif 'topic' in record_dict and 'article_count' in record_dict:
                print(f"     {i}. {record_dict['topic']} ({record_dict['article_count']} articles)")
            elif 'organization' in record_dict and 'article_count' in record_dict:
                print(f"     {i}. {record_dict['organization']} ({record_dict['article_count']} articles)")
            elif 'author' in record_dict and 'article_count' in record_dict:
                print(f"     {i}. {record_dict['author']} ({record_dict['article_count']} articles)")
            else:
                # Generic display
                display_items = []
                for key, value in record_dict.items():
                    if isinstance(value, (str, int, float)) and len(str(value)) < 100:
                        display_items.append(f"{key}: {value}")
                    elif isinstance(value, list) and len(value) < 5:
                        display_items.append(f"{key}: {value}")
                
                display_str = ", ".join(display_items[:3])
                if len(display_str) > 100:
                    display_str = display_str[:97] + "..."
                
                print(f"     {i}. {display_str}")
        
        if len(records) > 3:
            print(f"     ... and {len(records) - 3} more results")
    
    def run_all_examples(self):
        """Run all query examples"""
        print("🚀 Running all Cypher query examples for News Knowledge Graph")
        print("="*80)
        
        try:
            self.run_basic_queries()
            self.run_filtering_queries()
            self.run_relationship_queries()
            self.run_text_search_queries()
            self.run_aggregation_queries()
            self.run_geospatial_queries()
            self.run_temporal_queries()
            self.run_vector_search_examples()
            
            print("\n" + "="*80)
            print("🎉 All Cypher query examples completed!")
            
        except Exception as e:
            print(f"\n❌ Error running examples: {e}")
    
    def close(self):
        """Close Neo4j connection"""
        self.config.close()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run sample Cypher queries for news knowledge graph')
    parser.add_argument('--config', default='config.env', help='Configuration file path')
    parser.add_argument('--basic', action='store_true', help='Run basic queries only')
    parser.add_argument('--filtering', action='store_true', help='Run filtering queries only')
    parser.add_argument('--relationships', action='store_true', help='Run relationship queries only')
    parser.add_argument('--text-search', action='store_true', help='Run text search queries only')
    parser.add_argument('--aggregation', action='store_true', help='Run aggregation queries only')
    parser.add_argument('--geospatial', action='store_true', help='Run geospatial queries only')
    parser.add_argument('--temporal', action='store_true', help='Run temporal queries only')
    parser.add_argument('--vector-search', action='store_true', help='Run vector search examples only')
    
    args = parser.parse_args()
    
    try:
        # Create query examples
        examples = NewsQueryExamplesNeo4j(args.config)
        
        # Run specific examples or all
        if args.basic:
            examples.run_basic_queries()
        elif args.filtering:
            examples.run_filtering_queries()
        elif args.relationships:
            examples.run_relationship_queries()
        elif args.text_search:
            examples.run_text_search_queries()
        elif args.aggregation:
            examples.run_aggregation_queries()
        elif args.geospatial:
            examples.run_geospatial_queries()
        elif args.temporal:
            examples.run_temporal_queries()
        elif args.vector_search:
            examples.run_vector_search_examples()
        else:
            # Run all examples
            examples.run_all_examples()
        
        # Close connection
        examples.close()
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()