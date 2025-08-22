#!/usr/bin/env python3
"""
Vector Similarity Search for Neo4j News Knowledge Graph

This script provides vector similarity search capabilities for finding similar articles
using semantic embeddings stored in Neo4j.
"""

import os
import sys
import argparse
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from neo4j_config import load_neo4j_config
from ai_provider import get_ai_provider

# Load environment variables
load_dotenv()

class NewsVectorSearchNeo4j:
    """Vector similarity search for Neo4j news knowledge graph"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize the vector search"""
        self.config = load_neo4j_config(config_file)
        self.driver = self.config.get_driver()
        self.database = self.config.get_database()
        self.ai_provider = get_ai_provider()
        
        print(f"🧠 Vector search initialized for Neo4j")
        print(f"  AI Provider: {self.ai_provider.__class__.__name__}")
    
    def search(self, query_text: str, limit: int = 10, min_score: float = 0.5) -> List[Dict[str, Any]]:
        """
        Search for similar articles using vector similarity
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results
            min_score: Minimum similarity score (0-1)
        
        Returns:
            List of similar articles with scores
        """
        try:
            # Generate embedding for the query text
            print(f"🔍 Generating embedding for query: '{query_text[:50]}...'")
            query_embedding = self.ai_provider.generate_embedding(query_text)
            
            if not query_embedding:
                print("❌ Failed to generate embedding")
                return []
            
            # Search using vector index
            search_query = """
            CALL db.index.vector.queryNodes('article_embeddings', $topK, $queryVector)
            YIELD node, score
            WHERE score >= $minScore
            RETURN node.uri as uri,
                   node.title as title, 
                   node.abstract as abstract,
                   node.published as published,
                   node.url as url,
                   score
            ORDER BY score DESC
            LIMIT $limit
            """
            
            with self.driver.session(database=self.database) as session:
                result = session.run(search_query, {
                    'queryVector': query_embedding,
                    'topK': limit * 2,  # Get more candidates to filter by min_score
                    'minScore': min_score,
                    'limit': limit
                })
                
                articles = []
                for record in result:
                    articles.append({
                        'uri': record['uri'],
                        'title': record['title'],
                        'abstract': record['abstract'],
                        'published': record['published'],
                        'url': record['url'],
                        'score': record['score']
                    })
                
                print(f"✅ Found {len(articles)} similar articles")
                return articles
                
        except Exception as e:
            print(f"❌ Vector search failed: {e}")
            return []
    
    def search_by_topic(self, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for articles by topic using vector similarity
        
        Args:
            topic: Topic to search for
            limit: Maximum number of results
        
        Returns:
            List of articles related to the topic
        """
        # Use topic as the search text
        return self.search(f"articles about {topic}", limit)
    
    def find_similar_articles(self, article_uri: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find articles similar to a given article
        
        Args:
            article_uri: URI of the reference article
            limit: Maximum number of results
        
        Returns:
            List of similar articles
        """
        try:
            # Get the embedding of the reference article
            get_article_query = """
            MATCH (a:Article {uri: $uri})
            RETURN a.embedding as embedding, a.title as title
            """
            
            with self.driver.session(database=self.database) as session:
                result = session.run(get_article_query, {'uri': article_uri})
                record = result.single()
                
                if not record or not record['embedding']:
                    print(f"❌ Article not found or has no embedding: {article_uri}")
                    return []
                
                reference_embedding = record['embedding']
                reference_title = record['title']
                
                print(f"🔍 Finding articles similar to: '{reference_title}'")
                
                # Search for similar articles
                similar_query = """
                CALL db.index.vector.queryNodes('article_embeddings', $topK, $queryVector)
                YIELD node, score
                WHERE node.uri <> $excludeUri  // Exclude the reference article
                RETURN node.uri as uri,
                       node.title as title,
                       node.abstract as abstract,
                       node.published as published,
                       node.url as url,
                       score
                ORDER BY score DESC
                LIMIT $limit
                """
                
                result = session.run(similar_query, {
                    'queryVector': reference_embedding,
                    'topK': limit + 5,  # Get extra to account for filtering
                    'excludeUri': article_uri,
                    'limit': limit
                })
                
                articles = []
                for record in result:
                    articles.append({
                        'uri': record['uri'],
                        'title': record['title'],
                        'abstract': record['abstract'],
                        'published': record['published'],
                        'url': record['url'],
                        'score': record['score']
                    })
                
                print(f"✅ Found {len(articles)} similar articles")
                return articles
                
        except Exception as e:
            print(f"❌ Similar article search failed: {e}")
            return []
    
    def get_article_recommendations(self, user_interests: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get article recommendations based on user interests
        
        Args:
            user_interests: List of topics/interests
            limit: Maximum number of results
        
        Returns:
            List of recommended articles
        """
        if not user_interests:
            return []
        
        # Combine interests into a single query
        interests_text = " ".join(user_interests)
        search_text = f"articles about {interests_text}"
        
        print(f"🎯 Getting recommendations for interests: {interests_text}")
        return self.search(search_text, limit)
    
    def cluster_articles_by_similarity(self, threshold: float = 0.8, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find clusters of similar articles
        
        Args:
            threshold: Similarity threshold for clustering
            limit: Maximum number of articles to consider
        
        Returns:
            List of article clusters
        """
        try:
            print(f"🔄 Clustering articles with similarity threshold: {threshold}")
            
            # This is a simplified clustering approach
            # In practice, you might want to use more sophisticated clustering algorithms
            
            cluster_query = """
            MATCH (a1:Article)
            WHERE a1.embedding IS NOT NULL
            WITH a1
            LIMIT $limit
            
            CALL db.index.vector.queryNodes('article_embeddings', 10, a1.embedding)
            YIELD node as a2, score
            WHERE score >= $threshold AND a1.uri <> a2.uri
            
            RETURN a1.uri as article1_uri, 
                   a1.title as article1_title,
                   collect({uri: a2.uri, title: a2.title, score: score}) as similar_articles
            ORDER BY size(similar_articles) DESC
            LIMIT 10
            """
            
            with self.driver.session(database=self.database) as session:
                result = session.run(cluster_query, {
                    'threshold': threshold,
                    'limit': limit
                })
                
                clusters = []
                for record in result:
                    clusters.append({
                        'main_article': {
                            'uri': record['article1_uri'],
                            'title': record['article1_title']
                        },
                        'similar_articles': record['similar_articles'],
                        'cluster_size': len(record['similar_articles']) + 1
                    })
                
                print(f"✅ Found {len(clusters)} article clusters")
                return clusters
                
        except Exception as e:
            print(f"❌ Article clustering failed: {e}")
            return []
    
    def close(self):
        """Close Neo4j connection"""
        self.config.close()
    
    def _display_results(self, articles: List[Dict[str, Any]], show_score: bool = True):
        """Display search results in a formatted way"""
        if not articles:
            print("   No articles found")
            return
        
        print(f"📰 Found {len(articles)} articles:")
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'No title')
            score = f" (score: {article.get('score', 0):.3f})" if show_score and 'score' in article else ""
            abstract = article.get('abstract', '')
            
            print(f"  {i}. {title}{score}")
            if abstract and len(abstract) > 0:
                abstract_preview = abstract[:100] + "..." if len(abstract) > 100 else abstract
                print(f"     {abstract_preview}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Vector similarity search for news articles')
    parser.add_argument('query', nargs='?', help='Search query text')
    parser.add_argument('--config', default='config.env', help='Configuration file path')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of results')
    parser.add_argument('--min-score', type=float, default=0.5, help='Minimum similarity score')
    parser.add_argument('--topic', action='store_true', help='Search by topic')
    parser.add_argument('--similar', help='Find articles similar to given URI')
    parser.add_argument('--recommend', nargs='+', help='Get recommendations based on interests')
    parser.add_argument('--cluster', action='store_true', help='Find article clusters')
    
    args = parser.parse_args()
    
    try:
        # Create vector search
        vector_search = NewsVectorSearchNeo4j(args.config)
        
        if args.cluster:
            # Find article clusters
            clusters = vector_search.cluster_articles_by_similarity()
            print(f"\n🔗 Article Clusters:")
            for i, cluster in enumerate(clusters, 1):
                main = cluster['main_article']
                similar = cluster['similar_articles']
                print(f"  {i}. Main: {main['title']}")
                print(f"     Similar articles: {len(similar)}")
                for sim in similar[:3]:
                    print(f"       - {sim['title']} (score: {sim['score']:.3f})")
        
        elif args.similar:
            # Find similar articles
            results = vector_search.find_similar_articles(args.similar, args.limit)
            vector_search._display_results(results)
        
        elif args.recommend:
            # Get recommendations
            results = vector_search.get_article_recommendations(args.recommend, args.limit)
            vector_search._display_results(results)
        
        elif args.query:
            if args.topic:
                # Search by topic
                results = vector_search.search_by_topic(args.query, args.limit)
            else:
                # Regular search
                results = vector_search.search(args.query, args.limit, args.min_score)
            
            vector_search._display_results(results)
        
        else:
            print("❌ Please provide a search query or use --help for options")
        
        # Close connection
        vector_search.close()
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()