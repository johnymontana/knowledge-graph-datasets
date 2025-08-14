#!/usr/bin/env python3
"""
News Embeddings Generator for Dgraph Knowledge Graph

This script queries articles from Dgraph, generates AI embeddings for abstracts,
and updates the articles with the generated embeddings.
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any, Optional
from tqdm import tqdm
import pydgraph
from dotenv import load_dotenv

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dgraph_config import load_dgraph_config
from ai_provider import get_ai_provider

# Load environment variables
load_dotenv()

class NewsEmbeddingsGenerator:
    """Class for generating and updating embeddings for news articles"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize the embeddings generator"""
        self.config = load_dgraph_config(config_file)
        self.dgraph_client = self._create_dgraph_client()
        self.ai_provider = get_ai_provider()
        
        # Configuration from environment
        self.batch_size = int(os.getenv('EMBEDDING_BATCH_SIZE', '50'))
        
        print(f"🔧 Configuration loaded:")
        print(f"  Embedding batch size: {self.batch_size}")
        print(f"  AI Provider: {self.ai_provider.__class__.__name__}")
    
    def _create_dgraph_client(self) -> pydgraph.DgraphClient:
        """Create and return a Dgraph client"""
        try:
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
        except Exception as e:
            print(f"❌ Failed to create Dgraph client: {e}")
            raise
    
    def query_articles_without_embeddings(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Query articles from Dgraph that don't have embeddings
        
        Args:
            limit: Maximum number of articles to retrieve
            
        Returns:
            List of article data with UIDs and abstracts
        """
        query = """
        query articles($limit: int) {
            articles(func: type(Article), first: $limit) @filter(NOT has(Article.embedding)) {
                uid
                Article.title
                Article.abstract
                Article.uri
            }
        }
        """
        variables = {"$limit": str(limit)}
        
        try:
            res = self.dgraph_client.txn(read_only=True).query(query, variables=variables)
            articles = json.loads(res.json)['articles']
            print(f"📊 Retrieved {len(articles)} articles without embeddings from Dgraph")
            return articles
        except Exception as e:
            print(f"❌ Error querying Dgraph: {e}")
            return []
    
    def query_articles_by_topic(self, topic: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query articles by topic that don't have embeddings
        
        Args:
            topic: Topic to search for
            limit: Maximum number of articles to retrieve
            
        Returns:
            List of article data with UIDs and abstracts
        """
        query = """
        query articles_by_topic($topic: string, $limit: int) {
            articles(func: type(Article), first: $limit) @filter(
                NOT has(Article.embedding) AND 
                has(Article.topic) AND 
                anyoftext(Article.topic, $topic)
            ) {
                uid
                Article.title
                Article.abstract
                Article.uri
                Article.topic {
                    Topic.name
                }
            }
        }
        """
        variables = {"$topic": topic, "$limit": str(limit)}
        
        try:
            res = self.dgraph_client.txn(read_only=True).query(query, variables=variables)
            articles = json.loads(res.json)['articles']
            print(f"📊 Retrieved {len(articles)} articles about '{topic}' without embeddings")
            return articles
        except Exception as e:
            print(f"❌ Error querying Dgraph for topic '{topic}': {e}")
            return []
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate AI embedding for text
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            if not text or len(text.strip()) < 10:
                return None
            
            embedding = self.ai_provider.generate_embedding(text)
            return embedding
        except Exception as e:
            print(f"⚠️  Embedding generation failed: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors (None for failed ones)
        """
        try:
            # Try batch generation if supported
            if hasattr(self.ai_provider, 'generate_embeddings_batch'):
                embeddings = self.ai_provider.generate_embeddings_batch(texts)
                return embeddings
            else:
                # Fall back to individual generation
                embeddings = []
                for text in tqdm(texts, desc="Generating embeddings"):
                    embedding = self.generate_embedding(text)
                    embeddings.append(embedding)
                return embeddings
        except Exception as e:
            print(f"⚠️  Batch embedding generation failed: {e}")
            # Fall back to individual generation
            embeddings = []
            for text in tqdm(texts, desc="Generating embeddings (fallback)"):
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
            return embeddings
    
    def update_article_with_embedding(self, uid: str, embedding: List[float]) -> bool:
        """
        Update article in Dgraph with embedding
        
        Args:
            uid: UID of the article
            embedding: Embedding vector
            
        Returns:
            True if successful, False otherwise
        """
        if not embedding:
            return False
        
        # Convert embedding to JSON string to store in Dgraph
        embedding_json = json.dumps(embedding)
        
        mutation = {
            'set': [
                {
                    'uid': uid,
                    'Article.embedding': embedding_json
                }
            ]
        }
        
        try:
            txn = self.dgraph_client.txn()
            response = txn.mutate(set_obj=mutation['set'][0])
            txn.commit()
            return True
        except Exception as e:
            print(f"❌ Error updating Dgraph: {e}")
            return False
    
    def process_articles(self, articles: List[Dict[str, Any]], batch_size: Optional[int] = None) -> int:
        """
        Process articles, generate embeddings, and update Dgraph
        
        Args:
            articles: List of articles to process
            batch_size: Batch size for embedding generation (uses instance default if None)
            
        Returns:
            Number of successfully processed articles
        """
        if not articles:
            print("❌ No articles to process")
            return 0
        
        if batch_size is None:
            batch_size = self.batch_size
        
        print(f"🔄 Processing {len(articles)} articles in batches of {batch_size}")
        
        success_count = 0
        total_batches = (len(articles) + batch_size - 1) // batch_size
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} articles)")
            
            # Extract abstracts for this batch
            abstracts = []
            valid_articles = []
            
            for article in batch:
                abstract = article.get('Article.abstract', '')
                if abstract and len(abstract.strip()) >= 10:
                    abstracts.append(abstract)
                    valid_articles.append(article)
                else:
                    print(f"⚠️  Article {article.get('uid', 'unknown')} has no valid abstract, skipping")
            
            if not valid_articles:
                print(f"⚠️  No valid articles in batch {batch_num}")
                continue
            
            # Generate embeddings for this batch
            print(f"🧠 Generating embeddings for {len(valid_articles)} articles...")
            embeddings = self.generate_embeddings_batch(abstracts)
            
            # Update articles with embeddings
            print(f"💾 Updating articles with embeddings...")
            batch_success = 0
            
            for article, embedding in zip(valid_articles, embeddings):
                if embedding:
                    success = self.update_article_with_embedding(article['uid'], embedding)
                    if success:
                        batch_success += 1
                        success_count += 1
                    else:
                        print(f"⚠️  Failed to update article {article.get('uid', 'unknown')}")
                else:
                    print(f"⚠️  Failed to generate embedding for article {article.get('uid', 'unknown')}")
            
            print(f"✅ Batch {batch_num} complete: {batch_success}/{len(valid_articles)} articles updated")
        
        print(f"\n🎉 Processing complete! Successfully updated {success_count}/{len(articles)} articles")
        return success_count
    
    def generate_embeddings_for_all(self, limit: int = 10000) -> int:
        """
        Generate embeddings for all articles without embeddings
        
        Args:
            limit: Maximum number of articles to process
            
        Returns:
            Number of successfully processed articles
        """
        print(f"🚀 Starting embedding generation for up to {limit} articles")
        
        # Query articles without embeddings
        articles = self.query_articles_without_embeddings(limit)
        if not articles:
            print("✅ No articles found without embeddings")
            return 0
        
        # Process articles
        return self.process_articles(articles)
    
    def generate_embeddings_for_topic(self, topic: str, limit: int = 1000) -> int:
        """
        Generate embeddings for articles about a specific topic
        
        Args:
            topic: Topic to search for
            limit: Maximum number of articles to process
            
        Returns:
            Number of successfully processed articles
        """
        print(f"🚀 Starting embedding generation for articles about '{topic}' (limit: {limit})")
        
        # Query articles by topic without embeddings
        articles = self.query_articles_by_topic(topic, limit)
        if not articles:
            print(f"✅ No articles found about '{topic}' without embeddings")
            return 0
        
        # Process articles
        return self.process_articles(articles)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate embeddings for news articles in Dgraph')
    parser.add_argument('--config', default='config.env', help='Configuration file path')
    parser.add_argument('--topic', help='Generate embeddings only for articles about this topic')
    parser.add_argument('--limit', type=int, default=10000, help='Maximum number of articles to process')
    parser.add_argument('--batch-size', type=int, help='Batch size for embedding generation')
    
    args = parser.parse_args()
    
    try:
        # Create embeddings generator
        generator = NewsEmbeddingsGenerator(args.config)
        
        # Override batch size if provided
        if args.batch_size:
            generator.batch_size = args.batch_size
        
        # Generate embeddings
        if args.topic:
            success_count = generator.generate_embeddings_for_topic(args.topic, args.limit)
        else:
            success_count = generator.generate_embeddings_for_all(args.limit)
        
        if success_count > 0:
            print(f"🎉 Successfully generated embeddings for {success_count} articles!")
            sys.exit(0)
        else:
            print("⚠️  No articles were processed")
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
