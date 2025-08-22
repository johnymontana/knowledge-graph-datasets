#!/usr/bin/env python3
"""
Generate and Update Embeddings for Neo4j News Knowledge Graph

This script generates AI embeddings for articles stored in Neo4j and updates
the database with vector embeddings for semantic search.
"""

import os
import sys
import argparse
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from dotenv import load_dotenv

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from neo4j_config import load_neo4j_config
from ai_provider import get_ai_provider

# Load environment variables
load_dotenv()

class NewsEmbeddingsGeneratorNeo4j:
    """Generate and manage embeddings for Neo4j news articles"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize the embeddings generator"""
        self.config = load_neo4j_config(config_file)
        self.driver = self.config.get_driver()
        self.database = self.config.get_database()
        self.ai_provider = get_ai_provider()
        
        # Configuration from environment
        self.batch_size = int(os.getenv('EMBEDDING_BATCH_SIZE', '50'))
        
        print(f"🧠 Embeddings generator initialized:")
        print(f"  AI Provider: {self.ai_provider.__class__.__name__}")
        print(f"  Batch size: {self.batch_size}")
    
    def get_articles_without_embeddings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get articles that don't have embeddings yet"""
        query = """
        MATCH (a:Article)
        WHERE a.embedding IS NULL
        AND (a.title IS NOT NULL OR a.abstract IS NOT NULL)
        RETURN a.uri as uri, a.title as title, a.abstract as abstract
        ORDER BY a.published DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            articles = []
            
            for record in result:
                articles.append({
                    'uri': record['uri'],
                    'title': record['title'] or '',
                    'abstract': record['abstract'] or ''
                })
            
            return articles
    
    def get_articles_with_topic(self, topic: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get articles related to a specific topic"""
        query = """
        MATCH (a:Article)-[:HAS_TOPIC]->(t:Topic)
        WHERE toLower(t.name) CONTAINS toLower($topic)
        AND a.embedding IS NULL
        AND (a.title IS NOT NULL OR a.abstract IS NOT NULL)
        RETURN a.uri as uri, a.title as title, a.abstract as abstract
        ORDER BY a.published DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, {'topic': topic})
            articles = []
            
            for record in result:
                articles.append({
                    'uri': record['uri'],
                    'title': record['title'] or '',
                    'abstract': record['abstract'] or ''
                })
            
            return articles
    
    def _create_embedding_text(self, article: Dict[str, Any]) -> str:
        """Create text for embedding generation"""
        title = article.get('title', '').strip()
        abstract = article.get('abstract', '').strip()
        
        # Combine title and abstract
        if title and abstract:
            return f"{title}. {abstract}"
        elif title:
            return title
        elif abstract:
            return abstract
        else:
            return ""
    
    def generate_embeddings_batch(self, articles: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """Generate embeddings for a batch of articles"""
        # Prepare texts for embedding
        texts = []
        uris = []
        
        for article in articles:
            text = self._create_embedding_text(article)
            if text:
                texts.append(text)
                uris.append(article['uri'])
        
        if not texts:
            return {}
        
        try:
            # Generate embeddings
            embeddings = self.ai_provider.generate_embeddings_batch(texts)
            
            # Create URI to embedding mapping
            embeddings_map = {}
            for uri, embedding in zip(uris, embeddings):
                if embedding:  # Only include successful embeddings
                    embeddings_map[uri] = embedding
            
            return embeddings_map
            
        except Exception as e:
            print(f"❌ Batch embedding generation failed: {e}")
            # Fall back to individual generation
            embeddings_map = {}
            for article in articles:
                try:
                    text = self._create_embedding_text(article)
                    if text:
                        embedding = self.ai_provider.generate_embedding(text)
                        if embedding:
                            embeddings_map[article['uri']] = embedding
                except Exception as e:
                    print(f"⚠️  Failed to generate embedding for {article['uri']}: {e}")
            
            return embeddings_map
    
    def update_embeddings_in_neo4j(self, embeddings_map: Dict[str, List[float]]):
        """Update embeddings in Neo4j database"""
        if not embeddings_map:
            return
        
        update_query = """
        UNWIND $embeddings as embedding
        MATCH (a:Article {uri: embedding.uri})
        SET a.embedding = embedding.vector
        """
        
        # Prepare data for batch update
        embeddings_data = [
            {'uri': uri, 'vector': vector} 
            for uri, vector in embeddings_map.items()
        ]
        
        with self.driver.session(database=self.database) as session:
            session.run(update_query, {'embeddings': embeddings_data})
        
        print(f"✅ Updated {len(embeddings_map)} embeddings in Neo4j")
    
    def generate_embeddings_for_all(self, limit: Optional[int] = None):
        """Generate embeddings for all articles without them"""
        print("🔍 Finding articles without embeddings...")
        articles = self.get_articles_without_embeddings(limit)
        
        if not articles:
            print("✅ All articles already have embeddings!")
            return
        
        print(f"📊 Found {len(articles)} articles without embeddings")
        
        # Process in batches
        total_processed = 0
        total_successful = 0
        
        for i in tqdm(range(0, len(articles), self.batch_size), desc="Generating embeddings"):
            batch = articles[i:i + self.batch_size]
            
            # Generate embeddings for batch
            embeddings_map = self.generate_embeddings_batch(batch)
            
            # Update database
            if embeddings_map:
                self.update_embeddings_in_neo4j(embeddings_map)
                total_successful += len(embeddings_map)
            
            total_processed += len(batch)
        
        print(f"✅ Processed {total_processed} articles")
        print(f"✅ Successfully generated {total_successful} embeddings")
        
        # Update vector index
        self._update_vector_index()
    
    def generate_embeddings_for_topic(self, topic: str, limit: Optional[int] = None):
        """Generate embeddings for articles related to a specific topic"""
        print(f"🔍 Finding articles about '{topic}' without embeddings...")
        articles = self.get_articles_with_topic(topic, limit)
        
        if not articles:
            print(f"✅ No articles about '{topic}' need embeddings!")
            return
        
        print(f"📊 Found {len(articles)} articles about '{topic}' without embeddings")
        
        # Process in batches
        total_processed = 0
        total_successful = 0
        
        for i in tqdm(range(0, len(articles), self.batch_size), desc=f"Generating embeddings for {topic}"):
            batch = articles[i:i + self.batch_size]
            
            # Generate embeddings for batch
            embeddings_map = self.generate_embeddings_batch(batch)
            
            # Update database
            if embeddings_map:
                self.update_embeddings_in_neo4j(embeddings_map)
                total_successful += len(embeddings_map)
            
            total_processed += len(batch)
        
        print(f"✅ Processed {total_processed} articles about '{topic}'")
        print(f"✅ Successfully generated {total_successful} embeddings")
        
        # Update vector index
        self._update_vector_index()
    
    def regenerate_embeddings(self, force: bool = False):
        """Regenerate embeddings for all articles"""
        if force:
            print("🔄 Regenerating ALL embeddings (forced)...")
            query = """
            MATCH (a:Article)
            WHERE (a.title IS NOT NULL OR a.abstract IS NOT NULL)
            RETURN a.uri as uri, a.title as title, a.abstract as abstract
            ORDER BY a.published DESC
            """
        else:
            print("🔄 This will regenerate embeddings for articles that already have them.")
            response = input("Are you sure? (y/N): ")
            if response.lower() != 'y':
                print("❌ Operation cancelled")
                return
            
            query = """
            MATCH (a:Article)
            WHERE (a.title IS NOT NULL OR a.abstract IS NOT NULL)
            RETURN a.uri as uri, a.title as title, a.abstract as abstract
            ORDER BY a.published DESC
            """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            articles = []
            
            for record in result:
                articles.append({
                    'uri': record['uri'],
                    'title': record['title'] or '',
                    'abstract': record['abstract'] or ''
                })
        
        print(f"📊 Found {len(articles)} articles to process")
        
        # Process in batches
        total_processed = 0
        total_successful = 0
        
        for i in tqdm(range(0, len(articles), self.batch_size), desc="Regenerating embeddings"):
            batch = articles[i:i + self.batch_size]
            
            # Generate embeddings for batch
            embeddings_map = self.generate_embeddings_batch(batch)
            
            # Update database
            if embeddings_map:
                self.update_embeddings_in_neo4j(embeddings_map)
                total_successful += len(embeddings_map)
            
            total_processed += len(batch)
        
        print(f"✅ Processed {total_processed} articles")
        print(f"✅ Successfully regenerated {total_successful} embeddings")
        
        # Update vector index
        self._update_vector_index()
    
    def _update_vector_index(self):
        """Update or recreate the vector index"""
        try:
            print("🔄 Updating vector index...")
            self.config.create_vector_index()
            print("✅ Vector index updated")
        except Exception as e:
            print(f"⚠️  Vector index update issue: {e}")
    
    def get_embedding_statistics(self):
        """Get statistics about embeddings in the database"""
        stats_query = """
        MATCH (a:Article)
        RETURN 
            count(a) as total_articles,
            count(a.embedding) as articles_with_embeddings,
            count(a) - count(a.embedding) as articles_without_embeddings
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(stats_query)
            record = result.single()
            
            total = record['total_articles']
            with_embeddings = record['articles_with_embeddings']
            without_embeddings = record['articles_without_embeddings']
            
            percentage = (with_embeddings / total * 100) if total > 0 else 0
            
            print(f"📊 Embedding Statistics:")
            print(f"  Total articles: {total}")
            print(f"  With embeddings: {with_embeddings} ({percentage:.1f}%)")
            print(f"  Without embeddings: {without_embeddings}")
    
    def close(self):
        """Close Neo4j connection"""
        self.config.close()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate embeddings for Neo4j news articles')
    parser.add_argument('--config', default='config.env', help='Configuration file path')
    parser.add_argument('--limit', type=int, help='Maximum number of articles to process')
    parser.add_argument('--topic', help='Generate embeddings only for articles about this topic')
    parser.add_argument('--batch-size', type=int, help='Batch size for processing')
    parser.add_argument('--regenerate', action='store_true', help='Regenerate all embeddings')
    parser.add_argument('--force', action='store_true', help='Force regeneration without confirmation')
    parser.add_argument('--stats', action='store_true', help='Show embedding statistics only')
    
    args = parser.parse_args()
    
    try:
        # Create embeddings generator
        generator = NewsEmbeddingsGeneratorNeo4j(args.config)
        
        # Override batch size if specified
        if args.batch_size:
            generator.batch_size = args.batch_size
        
        if args.stats:
            # Show statistics only
            generator.get_embedding_statistics()
        
        elif args.regenerate:
            # Regenerate all embeddings
            generator.regenerate_embeddings(args.force)
        
        elif args.topic:
            # Generate embeddings for specific topic
            generator.generate_embeddings_for_topic(args.topic, args.limit)
        
        else:
            # Generate embeddings for articles without them
            generator.generate_embeddings_for_all(args.limit)
        
        # Show final statistics
        if not args.stats:
            generator.get_embedding_statistics()
        
        # Close connection
        generator.close()
        
        print("🎉 Embeddings generation completed!")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()