#!/usr/bin/env python3
"""
Sample Queries for News Knowledge Graph

This script demonstrates various query patterns for the news knowledge graph,
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

from dgraph_config import load_dgraph_config
from vector_search import NewsVectorSearch

# Load environment variables
load_dotenv()

class NewsQueryExamples:
    """Class containing example queries for the news knowledge graph"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize the query examples"""
        self.config = load_dgraph_config(config_file)
        self.vector_search = NewsVectorSearch(config_file)
        
        print(f"🔧 Configuration loaded for query examples")
    
    def run_basic_queries(self):
        """Run basic queries to explore the knowledge graph"""
        print("\n" + "="*60)
        print("📚 BASIC QUERIES")
        print("="*60)
        
        # Query 1: Get all articles
        print("\n1. Getting all articles...")
        query1 = """
        {
          articles(func: type(Article), first: 5) {
            uid
            Article.title
            Article.abstract
            Article.published
          }
        }
        """
        self._execute_query(query1, "Basic articles query")
        
        # Query 2: Get all topics
        print("\n2. Getting all topics...")
        query2 = """
        {
          topics(func: type(Topic), first: 10) {
            uid
            Topic.name
            count(~Article.topic)
          }
        }
        """
        self._execute_query(query2, "Topics with article counts")
        
        # Query 3: Get all organizations
        print("\n3. Getting all organizations...")
        query3 = """
        {
          organizations(func: type(Organization), first: 10) {
            uid
            Organization.name
            count(~Article.org)
          }
        }
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
        {
          articles(func: type(Article), first: 5) @filter(has(Article.abstract)) {
            uid
            Article.title
            Article.abstract
          }
        }
        """
        self._execute_query(query1, "Articles with abstracts")
        
        # Query 2: Articles with embeddings
        print("\n2. Articles with embeddings...")
        query2 = """
        {
          articles(func: type(Article), first: 5) @filter(has(Article.embedding)) {
            uid
            Article.title
            Article.abstract
          }
        }
        """
        self._execute_query(query2, "Articles with embeddings")
        
        # Query 3: Articles with topics
        print("\n3. Articles with topics...")
        query3 = """
        {
          articles(func: type(Article), first: 5) @filter(has(Article.topic)) {
            uid
            Article.title
            Article.topic {
              Topic.name
            }
          }
        }
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
        {
          articles(func: type(Article), first: 3) {
            uid
            Article.title
            Article.abstract
            Article.topic {
              Topic.name
            }
            Article.org {
              Organization.name
            }
            Article.person {
              Person.name
            }
            Article.geo {
              Geo.name
            }
            Article.author {
              Author.name
            }
          }
        }
        """
        self._execute_query(query1, "Articles with all relationships")
        
        # Query 2: Topics with their articles
        print("\n2. Topics with their articles...")
        query2 = """
        {
          topics(func: type(Topic), first: 5) {
            uid
            Topic.name
            ~Article.topic {
              Article.title
              Article.published
            }
          }
        }
        """
        self._execute_query(query2, "Topics with articles")
        
        # Query 3: Organizations with their articles
        print("\n3. Organizations with their articles...")
        query3 = """
        {
          organizations(func: type(Organization), first: 5) {
            uid
            Organization.name
            ~Article.org {
              Article.title
              Article.published
            }
          }
        }
        """
        self._execute_query(query3, "Organizations with articles")
    
    def run_text_search_queries(self):
        """Run text search queries"""
        print("\n" + "="*60)
        print("🔤 TEXT SEARCH QUERIES")
        print("="*60)
        
        # Query 1: Full-text search in abstracts
        print("\n1. Full-text search in abstracts...")
        query1 = """
        {
          articles(func: anyoftext(Article.abstract, "technology AI"), first: 5) {
            uid
            Article.title
            Article.abstract
          }
        }
        """
        self._execute_query(query1, "Full-text search for 'technology AI'")
        
        # Query 2: Term search in abstracts
        print("\n2. Term search in abstracts...")
        query2 = """
        {
          articles(func: anyofterms(Article.abstract, "climate change"), first: 5) {
            uid
            Article.title
            Article.abstract
          }
        }
        """
        self._execute_query(query2, "Term search for 'climate change'")
        
        # Query 3: Search in topic names
        print("\n3. Search in topic names...")
        query3 = """
        {
          topics(func: anyoftext(Topic.name, "politics"), first: 5) {
            uid
            Topic.name
            ~Article.topic {
              Article.title
            }
          }
        }
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
        {
          topics(func: type(Topic)) {
            uid
            Topic.name
            article_count: count(~Article.topic)
          }
        }
        """
        self._execute_query(query1, "Article count by topic")
        
        # Query 2: Count articles by organization
        print("\n2. Count articles by organization...")
        query2 = """
        {
          organizations(func: type(Organization)) {
            uid
            Organization.name
            article_count: count(~Article.org)
          }
        }
        """
        self._execute_query(query2, "Article count by organization")
        
        # Query 3: Count articles by author
        print("\n3. Count articles by author...")
        query3 = """
        {
          authors(func: type(Author)) {
            uid
            Author.name
            article_count: count(~Author.article)
          }
        }
        """
        self._execute_query(query3, "Article count by author")
    
    def run_vector_search_examples(self):
        """Run vector similarity search examples"""
        print("\n" + "="*60)
        print("🧠 VECTOR SIMILARITY SEARCH")
        print("="*60)
        
        # Example 1: Search for technology articles
        print("\n1. Searching for technology articles...")
        try:
            results = self.vector_search.search("artificial intelligence and machine learning", limit=3)
            if results:
                print(f"✅ Found {len(results)} technology articles")
                for i, article in enumerate(results, 1):
                    print(f"   {i}. {article.get('Article.title', 'No title')}")
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
                    print(f"   {i}. {article.get('Article.title', 'No title')}")
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
                    print(f"   {i}. {article.get('Article.title', 'No title')}")
            else:
                print("⚠️  No political articles found")
        except Exception as e:
            print(f"❌ Vector search failed: {e}")
    
    def _execute_query(self, query: str, description: str):
        """Execute a DQL query and display results"""
        try:
            # Try to use pydgraph client first
            import pydgraph
            
            # Create gRPC channel with options for large messages
            channel_options = [
                ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
                ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50MB
                ('grpc.max_metadata_size', 32 * 1024)  # 32KB
            ]
            
            client_stub = pydgraph.DgraphClientStub(
                self.config.get_grpc_url(), 
                options=channel_options
            )
            dgraph_client = pydgraph.DgraphClient(client_stub)
            
            # Execute query
            res = dgraph_client.txn(read_only=True).query(query)
            results = json.loads(res.json)
            
            print(f"✅ {description}")
            self._display_results(results)
            
        except ImportError:
            # Fall back to HTTP API
            self._execute_http_query(query, description)
        except Exception as e:
            print(f"❌ Query failed: {e}")
    
    def _execute_http_query(self, query: str, description: str):
        """Execute a DQL query using HTTP API"""
        try:
            import requests
            
            url = f"{self.config.get_http_url()}/query"
            headers = self.config.get_headers()
            
            payload = {
                "query": query
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            results = response.json()
            
            print(f"✅ {description} (HTTP API)")
            self._display_results(results)
            
        except Exception as e:
            print(f"❌ HTTP query failed: {e}")
    
    def _display_results(self, results: Dict[str, Any]):
        """Display query results in a formatted way"""
        if not results or not results.get('data'):
            print("   No results found")
            return
        
        data = results['data']
        
        # Display results based on the query structure
        for key, value in data.items():
            if isinstance(value, list):
                print(f"   {key}: {len(value)} results")
                for i, item in enumerate(value[:3], 1):  # Show first 3 results
                    if isinstance(item, dict):
                        if 'Article.title' in item:
                            print(f"     {i}. {item['Article.title']}")
                        elif 'Topic.name' in item:
                            print(f"     {i}. {item['Topic.name']}")
                        elif 'Organization.name' in item:
                            print(f"     {i}. {item['Organization.name']}")
                        elif 'Author.name' in item:
                            print(f"     {i}. {item['Author.name']}")
                        else:
                            print(f"     {i}. {str(item)[:100]}...")
                    else:
                        print(f"     {i}. {str(item)[:100]}...")
                
                if len(value) > 3:
                    print(f"     ... and {len(value) - 3} more results")
            else:
                print(f"   {key}: {value}")
    
    def run_all_examples(self):
        """Run all query examples"""
        print("🚀 Running all query examples for News Knowledge Graph")
        print("="*80)
        
        try:
            self.run_basic_queries()
            self.run_filtering_queries()
            self.run_relationship_queries()
            self.run_text_search_queries()
            self.run_aggregation_queries()
            self.run_vector_search_examples()
            
            print("\n" + "="*80)
            print("🎉 All query examples completed!")
            
        except Exception as e:
            print(f"\n❌ Error running examples: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run sample queries for news knowledge graph')
    parser.add_argument('--config', default='config.env', help='Configuration file path')
    parser.add_argument('--basic', action='store_true', help='Run basic queries only')
    parser.add_argument('--filtering', action='store_true', help='Run filtering queries only')
    parser.add_argument('--relationships', action='store_true', help='Run relationship queries only')
    parser.add_argument('--text-search', action='store_true', help='Run text search queries only')
    parser.add_argument('--aggregation', action='store_true', help='Run aggregation queries only')
    parser.add_argument('--vector-search', action='store_true', help='Run vector search examples only')
    
    args = parser.parse_args()
    
    try:
        # Create query examples
        examples = NewsQueryExamples(args.config)
        
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
        elif args.vector_search:
            examples.run_vector_search_examples()
        else:
            # Run all examples
            examples.run_all_examples()
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
