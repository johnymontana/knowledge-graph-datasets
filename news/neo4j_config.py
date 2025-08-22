"""
Neo4j Configuration Module for News Knowledge Graph

Handles Neo4j connection configuration and management.
Supports both local and remote Neo4j instances with authentication.
"""

import os
import re
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
from neo4j import GraphDatabase

class Neo4jConfig:
    """Configuration manager for Neo4j connections"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize configuration from file"""
        self.config_file = config_file
        self.uri = None
        self.username = None
        self.password = None
        self.database = None
        self.driver = None
        
        # Load configuration
        self._load_config()
        self._create_driver()
    
    def _load_config(self):
        """Load configuration from environment file"""
        # Try to load from config.env first
        if os.path.exists(self.config_file):
            load_dotenv(self.config_file)
        else:
            # Fall back to .env if config.env doesn't exist
            load_dotenv()
        
        # Get configuration from environment
        self.uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD', 'password')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')
        
        print(f"🔧 Neo4j Configuration:")
        print(f"  URI: {self.uri}")
        print(f"  Username: {self.username}")
        print(f"  Database: {self.database}")
    
    def _create_driver(self):
        """Create Neo4j driver"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password),
                max_connection_pool_size=16,
                connection_timeout=30.0,
                max_transaction_retry_time=30.0
            )
            # Test connection
            self.driver.verify_connectivity()
            print(f"✅ Successfully connected to Neo4j")
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            raise
    
    def get_driver(self):
        """Get Neo4j driver instance"""
        return self.driver
    
    def get_database(self) -> str:
        """Get database name"""
        return self.database
    
    def close(self):
        """Close Neo4j driver"""
        if self.driver:
            self.driver.close()
    
    def test_connection(self) -> bool:
        """Test Neo4j connection"""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def create_indexes(self):
        """Create necessary indexes for the news graph"""
        indexes = [
            # Article indexes
            "CREATE INDEX article_uri IF NOT EXISTS FOR (a:Article) ON (a.uri)",
            "CREATE INDEX article_title IF NOT EXISTS FOR (a:Article) ON (a.title)",
            "CREATE INDEX article_published IF NOT EXISTS FOR (a:Article) ON (a.published)",
            "CREATE FULLTEXT INDEX article_text IF NOT EXISTS FOR (a:Article) ON EACH [a.title, a.abstract]",
            
            # Topic indexes
            "CREATE INDEX topic_name IF NOT EXISTS FOR (t:Topic) ON (t.name)",
            
            # Organization indexes
            "CREATE INDEX organization_name IF NOT EXISTS FOR (o:Organization) ON (o.name)",
            
            # Person indexes
            "CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)",
            
            # Author indexes
            "CREATE INDEX author_name IF NOT EXISTS FOR (a:Author) ON (a.name)",
            
            # Geo indexes
            "CREATE INDEX geo_name IF NOT EXISTS FOR (g:Geo) ON (g.name)",
        ]
        
        with self.driver.session(database=self.database) as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    print(f"✅ Created/verified index")
                except Exception as e:
                    print(f"⚠️  Index creation issue (may already exist): {e}")
    
    def create_vector_index(self):
        """Create vector index for embeddings"""
        vector_index_query = """
        CREATE VECTOR INDEX article_embeddings IF NOT EXISTS
        FOR (a:Article) ON (a.embedding)
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }
        }
        """
        
        with self.driver.session(database=self.database) as session:
            try:
                session.run(vector_index_query)
                print("✅ Created/verified vector index for embeddings")
            except Exception as e:
                print(f"⚠️  Vector index creation issue: {e}")

def load_neo4j_config(config_file: str = "config.env") -> Neo4jConfig:
    """Load Neo4j configuration"""
    return Neo4jConfig(config_file)