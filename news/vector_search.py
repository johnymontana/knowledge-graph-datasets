#!/usr/bin/env python3
"""
Vector Similarity Search for News Knowledge Graph

This script performs vector similarity search in Dgraph using AI-generated embeddings.
Takes a string input, generates an embedding, and finds similar articles.
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
from ai_provider import get_ai_provider

# Load environment variables
load_dotenv()

class NewsVectorSearch:
    """Class for performing vector similarity search on news articles"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize the vector search"""
        self.config = load_dgraph_config(config_file)
        self.dgraph_client = self._create_dgraph_client()
        self.ai_provider = get_ai_provider()
        
        print(f"🔧 Configuration loaded:")
        print(f"  AI Provider: {self.ai_provider.__class__.__name__}")
    
    def _create_dgraph_client(self):
        """Create and return a Dgraph client"""
        try:
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
            return pydgraph.DgraphClient(client_stub)
        except ImportError:
            print("❌ pydgraph not available, using HTTP API instead")
            return None
        except Exception as e:
            print(f"❌ Failed to create Dgraph client: {e}")
            return None
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate AI embedding for text
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            if not text or len(text.strip()) < 3:
                return None
            
            embedding = self.ai_provider.generate_embedding(text)
            return embedding
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            return None
    
    def vector_similarity_search(self, embedding: List[float], limit: int = 10, 
                               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search in Dgraph
        
        Args:
            embedding: Query embedding vector
            limit: Maximum number of results to return
            filters: Optional filters to apply to the search
            
        Returns:
            List of similar articles
        """
        if not embedding:
            return []
        
        # Convert embedding to JSON string for the query
        embedding_json = json.dumps(embedding)
        
        # Build the query with optional filters
        query = self._build_search_query(limit, filters)
        variables = {"$embedding": embedding_json, "$limit": str(limit)}
        
        try:
            if self.dgraph_client:
                # Use pydgraph client
                res = self.dgraph_client.txn(read_only=True).query(query, variables=variables)
                results = json.loads(res.json)['articles']
            else:
                # Use HTTP API
                results = self._http_query(query, variables)
            
            # Results are already sorted by similarity score from the similar_to function
            return results
        except Exception as e:
            print(f"❌ Error performing vector search: {e}")
            return []
    
    def _build_search_query(self, limit: int, filters: Optional[Dict[str, Any]] = None) -> str:
        """Build the DQL query for vector search with optional filters"""
        base_query = """
        query vector_search($embedding: string, $limit: int) {
          articles(func: similar_to(Article.embedding, $limit, $embedding)) {
            uid
            Article.title
            Article.abstract
            Article.uri
            Article.url
            Article.published
            score
        """
        
        # Add filters if provided
        if filters:
            if filters.get('topic'):
                base_query += """
            Article.topic {
              Topic.name
            }
        """
            if filters.get('organization'):
                base_query += """
            Article.org {
              Organization.name
            }
        """
            if filters.get('author'):
                base_query += """
            Article.author {
              Author.name
            }
        """
            if filters.get('location'):
                base_query += """
            Article.geo {
              Geo.name
              Geo.location
            }
        """
            if filters.get('date_from') or filters.get('date_to'):
                base_query += """
            Article.published
        """
        
        base_query += """
          }
        }
        """
        
        return base_query
    
    def _http_query(self, query: str, variables: Dict[str, str]) -> List[Dict[str, Any]]:
        """Execute query using HTTP API"""
        import requests
        
        url = f"{self.config.get_http_url()}/query"
        headers = self.config.get_headers()
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get('data', {}).get('articles', [])
        except Exception as e:
            print(f"❌ HTTP query failed: {e}")
            return []
    
    def search(self, query_text: str, limit: int = 10, 
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar articles based on query text
        
        Args:
            query_text: Query text
            limit: Maximum number of results to return
            filters: Optional filters to apply
            
        Returns:
            List of similar articles
        """
        print(f"🔍 Searching for articles similar to: '{query_text}'")
        
        # Generate embedding for query text
        embedding = self.generate_embedding(query_text)
        if not embedding:
            print("❌ Failed to generate embedding for query text")
            return []
        
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        
        # Perform vector similarity search
        results = self.vector_similarity_search(embedding, limit, filters)
        return results
    
    def search_by_topic(self, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for articles by topic using vector similarity
        
        Args:
            topic: Topic to search for
            limit: Maximum number of results to return
            
        Returns:
            List of similar articles
        """
        filters = {"topic": True}
        return self.search(topic, limit, filters)
    
    def search_by_organization(self, org_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for articles by organization using vector similarity
        
        Args:
            org_name: Organization name to search for
            limit: Maximum number of results to return
            
        Returns:
            List of similar articles
        """
        filters = {"organization": True}
        return self.search(org_name, limit, filters)
    
    def search_by_location(self, location: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for articles by location using vector similarity
        
        Args:
            location: Location to search for
            limit: Maximum number of results to return
            
        Returns:
            List of similar articles
        """
        filters = {"location": True}
        return self.search(location, limit, filters)
    
    def display_results(self, results: List[Dict[str, Any]], query_text: str):
        """Display search results in a formatted way"""
        if not results:
            print(f"❌ No articles found similar to '{query_text}'")
            return
        
        print(f"\n📰 Found {len(results)} similar articles:")
        print("=" * 80)
        
        for i, article in enumerate(results, 1):
            print(f"\n{i}. {article.get('Article.title', 'No title')}")
            
            # Show score if available
            score = article.get('score', 0)
            if score > 0:
                print(f"   Similarity Score: {score:.4f}")
            
            # Show abstract
            abstract = article.get('Article.abstract', 'No abstract')
            if abstract and len(abstract) > 200:
                abstract = abstract[:200] + "..."
            print(f"   {abstract}")
            
            # Show metadata
            if article.get('Article.published'):
                print(f"   Published: {article['Article.published']}")
            
            if article.get('Article.uri'):
                print(f"   URI: {article['Article.uri']}")
            
            # Show related entities if available
            if article.get('Article.topic'):
                topics = [t.get('Topic.name', '') for t in article['Article.topic'] if t.get('Topic.name')]
                if topics:
                    print(f"   Topics: {', '.join(topics)}")
            
            if article.get('Article.org'):
                orgs = [o.get('Organization.name', '') for o in article['Article.org'] if o.get('Organization.name')]
                if orgs:
                    print(f"   Organizations: {', '.join(orgs)}")
            
            print("-" * 80)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Vector similarity search in news knowledge graph')
    parser.add_argument('query', help='Query text to search for similar articles')
    parser.add_argument('--config', default='config.env', help='Configuration file path')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of results to return')
    parser.add_argument('--topic', action='store_true', help='Search by topic')
    parser.add_argument('--organization', action='store_true', help='Search by organization')
    parser.add_argument('--location', action='store_true', help='Search by location')
    
    args = parser.parse_args()
    
    try:
        # Create searcher
        searcher = NewsVectorSearch(args.config)
        
        # Determine search type and filters
        filters = None
        if args.topic:
            filters = {"topic": True}
        elif args.organization:
            filters = {"organization": True}
        elif args.location:
            filters = {"location": True}
        
        # Perform search
        results = searcher.search(args.query, args.limit, filters)
        
        # Display results
        searcher.display_results(results, args.query)
        
        if results:
            print(f"\n✅ Search completed successfully!")
        else:
            print(f"\n⚠️  No results found")
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
