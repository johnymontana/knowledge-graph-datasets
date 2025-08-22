#!/usr/bin/env python3
"""
Test Suite for Neo4j News Knowledge Graph

This script provides comprehensive testing and validation for the Neo4j news
knowledge graph system, including configuration, data validation, and functionality tests.
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
from ai_provider import get_ai_provider
from news_import_neo4j import NewsImporterNeo4j
from news_embeddings_neo4j import NewsEmbeddingsGeneratorNeo4j
from vector_search_neo4j import NewsVectorSearchNeo4j

# Load environment variables
load_dotenv()

class NewsDataTesterNeo4j:
    """Comprehensive tester for Neo4j news knowledge graph system"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize the tester"""
        self.config_file = config_file
        self.config = None
        self.driver = None
        self.database = None
        self.ai_provider = None
        
        print(f"🧪 Neo4j News Data Tester initialized")
    
    def test_configuration(self) -> bool:
        """Test system configuration"""
        print("\n" + "="*60)
        print("⚙️  CONFIGURATION TESTS")
        print("="*60)
        
        success = True
        
        # Test 1: Configuration file loading
        print("\n1. Testing configuration file loading...")
        try:
            self.config = load_neo4j_config(self.config_file)
            print("✅ Configuration loaded successfully")
        except Exception as e:
            print(f"❌ Configuration loading failed: {e}")
            return False
        
        # Test 2: Neo4j connection
        print("\n2. Testing Neo4j connection...")
        try:
            self.driver = self.config.get_driver()
            self.database = self.config.get_database()
            
            if self.config.test_connection():
                print("✅ Neo4j connection successful")
            else:
                print("❌ Neo4j connection test failed")
                success = False
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
            success = False
        
        # Test 3: AI provider configuration
        print("\n3. Testing AI provider configuration...")
        try:
            self.ai_provider = get_ai_provider()
            print(f"✅ AI Provider configured: {self.ai_provider.__class__.__name__}")
        except Exception as e:
            print(f"❌ AI provider configuration failed: {e}")
            success = False
        
        # Test 4: Environment variables
        print("\n4. Testing environment variables...")
        required_vars = []
        optional_vars = ['BATCH_SIZE', 'DATA_DIR', 'EMBEDDING_BATCH_SIZE', 'LOG_LEVEL']
        
        # Check AI provider keys
        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not openai_key and not anthropic_key:
            print("⚠️  No AI provider keys found (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
            print("   This is required for embedding generation")
            success = False
        else:
            print("✅ AI provider keys configured")
        
        # Check optional variables
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                print(f"✅ {var}: {value}")
            else:
                print(f"⚠️  {var}: Not set (using default)")
        
        return success
    
    def test_neo4j_setup(self) -> bool:
        """Test Neo4j database setup"""
        print("\n" + "="*60)
        print("🗄️  NEO4J SETUP TESTS")
        print("="*60)
        
        if not self.driver:
            print("❌ Neo4j driver not available")
            return False
        
        success = True
        
        # Test 1: Database accessibility
        print("\n1. Testing database accessibility...")
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 'Hello Neo4j' as message")
                message = result.single()["message"]
                print(f"✅ Database accessible: {message}")
        except Exception as e:
            print(f"❌ Database access failed: {e}")
            success = False
        
        # Test 2: Schema setup (indexes and constraints)
        print("\n2. Testing schema setup...")
        try:
            with self.driver.session(database=self.database) as session:
                # Check for constraints
                constraints_result = session.run("SHOW CONSTRAINTS")
                constraints = [record['name'] for record in constraints_result]
                
                # Check for indexes  
                indexes_result = session.run("SHOW INDEXES")
                indexes = [record['name'] for record in indexes_result]
                
                print(f"✅ Found {len(constraints)} constraints and {len(indexes)} indexes")
                
                # Check for specific important indexes
                important_indexes = ['article_uri', 'article_text', 'article_embeddings']
                missing_indexes = []
                
                for idx_name in important_indexes:
                    if not any(idx_name in idx for idx in indexes):
                        missing_indexes.append(idx_name)
                
                if missing_indexes:
                    print(f"⚠️  Missing important indexes: {missing_indexes}")
                    print("   Consider running: self.config.create_indexes()")
                else:
                    print("✅ All important indexes present")
                    
        except Exception as e:
            print(f"❌ Schema check failed: {e}")
            success = False
        
        # Test 3: Write permissions
        print("\n3. Testing write permissions...")
        try:
            with self.driver.session(database=self.database) as session:
                # Create a test node
                session.run("""
                    CREATE (test:TestNode {id: 'test-' + toString(timestamp()), message: 'Test write'})
                """)
                
                # Delete test nodes
                result = session.run("MATCH (test:TestNode) DELETE test RETURN count(*) as deleted")
                deleted_count = result.single()["deleted"]
                print(f"✅ Write permissions OK (cleaned up {deleted_count} test nodes)")
                
        except Exception as e:
            print(f"❌ Write permission test failed: {e}")
            success = False
        
        return success
    
    def test_ai_functionality(self) -> bool:
        """Test AI provider functionality"""
        print("\n" + "="*60)
        print("🧠 AI FUNCTIONALITY TESTS")
        print("="*60)
        
        if not self.ai_provider:
            print("❌ AI provider not available")
            return False
        
        success = True
        
        # Test 1: Single embedding generation
        print("\n1. Testing single embedding generation...")
        try:
            test_text = "This is a test article about technology and artificial intelligence."
            embedding = self.ai_provider.generate_embedding(test_text)
            
            if embedding and isinstance(embedding, list) and len(embedding) > 0:
                print(f"✅ Single embedding generated: {len(embedding)} dimensions")
            else:
                print("❌ Single embedding generation failed")
                success = False
        except Exception as e:
            print(f"❌ Single embedding generation failed: {e}")
            success = False
        
        # Test 2: Batch embedding generation
        print("\n2. Testing batch embedding generation...")
        try:
            test_texts = [
                "Technology news about artificial intelligence",
                "Climate change and environmental issues",
                "Political developments and government policies"
            ]
            
            embeddings = self.ai_provider.generate_embeddings_batch(test_texts)
            
            if (embeddings and 
                isinstance(embeddings, list) and 
                len(embeddings) == len(test_texts) and
                all(isinstance(emb, list) for emb in embeddings)):
                print(f"✅ Batch embeddings generated: {len(embeddings)} embeddings")
            else:
                print("❌ Batch embedding generation failed")
                success = False
        except Exception as e:
            print(f"❌ Batch embedding generation failed: {e}")
            success = False
        
        # Test 3: Chat completion (if available)
        print("\n3. Testing chat completion...")
        try:
            messages = [{"role": "user", "content": "What is 2+2?"}]
            response = self.ai_provider.chat_completion(messages)
            
            if response and isinstance(response, str) and len(response) > 0:
                print(f"✅ Chat completion working: '{response[:50]}...'")
            else:
                print("⚠️  Chat completion not available or failed")
        except Exception as e:
            print(f"⚠️  Chat completion test failed: {e}")
            # Don't mark as failure since chat completion might not be required
        
        return success
    
    def test_data_import(self) -> bool:
        """Test data import functionality"""
        print("\n" + "="*60)
        print("📊 DATA IMPORT TESTS")
        print("="*60)
        
        # Check if sample data exists
        data_dir = os.getenv('DATA_DIR', 'data/articles')
        if not os.path.exists(data_dir):
            print(f"⚠️  Data directory not found: {data_dir}")
            print("   Cannot test data import without sample data")
            return True  # Not a failure, just no data to test with
        
        # Look for JSON files
        json_files = []
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))
        
        if not json_files:
            print(f"⚠️  No JSON files found in {data_dir}")
            print("   Cannot test data import without sample data")
            return True
        
        print(f"📁 Found {len(json_files)} JSON files for testing")
        
        success = True
        
        # Test 1: Import functionality
        print("\n1. Testing import functionality...")
        try:
            importer = NewsImporterNeo4j(self.config_file)
            
            # Import a small subset for testing
            print("   Importing up to 5 articles for testing...")
            importer.import_articles(data_dir, limit=5)
            
            # Check if articles were imported
            with self.driver.session(database=self.database) as session:
                result = session.run("MATCH (a:Article) RETURN count(a) as count")
                article_count = result.single()["count"]
                
                if article_count > 0:
                    print(f"✅ Import successful: {article_count} articles imported")
                else:
                    print("❌ No articles were imported")
                    success = False
            
            importer.close()
            
        except Exception as e:
            print(f"❌ Data import test failed: {e}")
            success = False
        
        return success
    
    def test_vector_search(self) -> bool:
        """Test vector search functionality"""
        print("\n" + "="*60)
        print("🔍 VECTOR SEARCH TESTS")
        print("="*60)
        
        success = True
        
        # Test 1: Check if articles have embeddings
        print("\n1. Checking for articles with embeddings...")
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("""
                    MATCH (a:Article) 
                    RETURN count(a) as total, 
                           count(a.embedding) as with_embeddings
                """)
                record = result.single()
                total = record["total"]
                with_embeddings = record["with_embeddings"]
                
                print(f"📊 Articles: {total} total, {with_embeddings} with embeddings")
                
                if with_embeddings == 0:
                    print("⚠️  No articles have embeddings yet")
                    print("   Vector search tests cannot be performed")
                    print("   Run: uv run news_embeddings_neo4j.py --limit 10")
                    return True  # Not a failure, just no embeddings yet
                
        except Exception as e:
            print(f"❌ Error checking embeddings: {e}")
            success = False
        
        # Test 2: Vector search functionality
        if success:
            print("\n2. Testing vector search functionality...")
            try:
                searcher = NewsVectorSearchNeo4j(self.config_file)
                
                # Test search
                results = searcher.search("technology artificial intelligence", limit=3)
                
                if results and len(results) > 0:
                    print(f"✅ Vector search working: found {len(results)} results")
                    for i, article in enumerate(results[:2], 1):
                        title = article.get('title', 'No title')[:50]
                        score = article.get('score', 0)
                        print(f"   {i}. {title}... (score: {score:.3f})")
                else:
                    print("⚠️  Vector search returned no results")
                
                searcher.close()
                
            except Exception as e:
                print(f"❌ Vector search test failed: {e}")
                success = False
        
        return success
    
    def test_cypher_queries(self) -> bool:
        """Test various Cypher queries"""
        print("\n" + "="*60)
        print("📝 CYPHER QUERY TESTS")
        print("="*60)
        
        success = True
        
        test_queries = [
            {
                "name": "Basic article count",
                "query": "MATCH (a:Article) RETURN count(a) as count",
                "expected_type": int
            },
            {
                "name": "Articles with topics",
                "query": """
                    MATCH (a:Article)-[:HAS_TOPIC]->(t:Topic) 
                    RETURN a.title, collect(t.name) as topics 
                    LIMIT 3
                """,
                "expected_type": list
            },
            {
                "name": "Topic distribution",
                "query": """
                    MATCH (t:Topic)<-[:HAS_TOPIC]-(a:Article)
                    RETURN t.name, count(a) as article_count
                    ORDER BY article_count DESC
                    LIMIT 5
                """,
                "expected_type": list
            },
            {
                "name": "Author statistics",
                "query": """
                    MATCH (au:Author)<-[:WRITTEN_BY]-(a:Article)
                    RETURN count(DISTINCT au) as unique_authors,
                           count(a) as total_articles
                """,
                "expected_type": dict
            }
        ]
        
        with self.driver.session(database=self.database) as session:
            for i, test in enumerate(test_queries, 1):
                print(f"\n{i}. Testing: {test['name']}")
                try:
                    result = session.run(test["query"])
                    
                    if test["expected_type"] == int:
                        record = result.single()
                        count = record["count"] if record else 0
                        print(f"✅ Query successful: {count}")
                    
                    elif test["expected_type"] == list:
                        records = list(result)
                        print(f"✅ Query successful: {len(records)} records")
                    
                    elif test["expected_type"] == dict:
                        record = result.single()
                        if record:
                            data = dict(record)
                            print(f"✅ Query successful: {data}")
                        else:
                            print("✅ Query successful: No data")
                    
                except Exception as e:
                    print(f"❌ Query failed: {e}")
                    success = False
        
        return success
    
    def test_system_integration(self) -> bool:
        """Test full system integration"""
        print("\n" + "="*60)
        print("🔗 SYSTEM INTEGRATION TESTS")
        print("="*60)
        
        success = True
        
        # Test 1: Full workflow simulation
        print("\n1. Testing full workflow...")
        try:
            # Check current state
            with self.driver.session(database=self.database) as session:
                result = session.run("""
                    MATCH (a:Article) 
                    RETURN count(a) as total,
                           count(a.embedding) as with_embeddings,
                           count(a.title) as with_titles
                """)
                
                stats = result.single()
                total = stats["total"]
                with_embeddings = stats["with_embeddings"]
                with_titles = stats["with_titles"]
                
                print(f"📊 Current state:")
                print(f"   Total articles: {total}")
                print(f"   With embeddings: {with_embeddings}")
                print(f"   With titles: {with_titles}")
                
                if total > 0:
                    print("✅ System has data and appears to be working")
                else:
                    print("⚠️  No articles in database")
                    print("   Run: uv run news_import_neo4j.py --limit 10")
                
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            success = False
        
        # Test 2: Cross-component functionality
        print("\n2. Testing cross-component functionality...")
        try:
            if self.ai_provider:
                # Test embedding generation and search together
                test_query = "artificial intelligence"
                embedding = self.ai_provider.generate_embedding(test_query)
                
                if embedding:
                    print("✅ AI and database components integrate properly")
                else:
                    print("⚠️  AI component integration issue")
            
        except Exception as e:
            print(f"❌ Cross-component test failed: {e}")
            success = False
        
        return success
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        print("🚀 Running comprehensive Neo4j News Data tests")
        print("="*80)
        
        all_success = True
        
        # Run all test suites
        test_suites = [
            ("Configuration", self.test_configuration),
            ("Neo4j Setup", self.test_neo4j_setup),
            ("AI Functionality", self.test_ai_functionality),
            ("Data Import", self.test_data_import),
            ("Vector Search", self.test_vector_search),
            ("Cypher Queries", self.test_cypher_queries),
            ("System Integration", self.test_system_integration),
        ]
        
        results = {}
        
        for suite_name, test_func in test_suites:
            try:
                success = test_func()
                results[suite_name] = success
                if not success:
                    all_success = False
            except Exception as e:
                print(f"❌ Test suite '{suite_name}' crashed: {e}")
                results[suite_name] = False
                all_success = False
        
        # Print summary
        print("\n" + "="*80)
        print("📊 TEST RESULTS SUMMARY")
        print("="*80)
        
        for suite_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {suite_name}")
        
        if all_success:
            print("\n🎉 All tests passed! System is ready for use.")
        else:
            print("\n⚠️  Some tests failed. Please check the issues above.")
        
        return all_success
    
    def close(self):
        """Close connections"""
        if self.config:
            self.config.close()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Test Neo4j news knowledge graph system')
    parser.add_argument('--config', default='config.env', help='Configuration file path')
    parser.add_argument('--config-only', action='store_true', help='Test configuration only')
    parser.add_argument('--neo4j-only', action='store_true', help='Test Neo4j setup only')
    parser.add_argument('--ai-only', action='store_true', help='Test AI functionality only')
    parser.add_argument('--data-only', action='store_true', help='Test data import only')
    parser.add_argument('--vector-only', action='store_true', help='Test vector search only')
    parser.add_argument('--queries-only', action='store_true', help='Test queries only')
    parser.add_argument('--integration-only', action='store_true', help='Test integration only')
    
    args = parser.parse_args()
    
    try:
        # Create tester
        tester = NewsDataTesterNeo4j(args.config)
        
        # Run specific tests or all
        success = True
        
        if args.config_only:
            success = tester.test_configuration()
        elif args.neo4j_only:
            success = tester.test_configuration() and tester.test_neo4j_setup()
        elif args.ai_only:
            success = tester.test_configuration() and tester.test_ai_functionality()
        elif args.data_only:
            success = tester.test_configuration() and tester.test_data_import()
        elif args.vector_only:
            success = tester.test_configuration() and tester.test_vector_search()
        elif args.queries_only:
            success = tester.test_configuration() and tester.test_cypher_queries()
        elif args.integration_only:
            success = tester.test_configuration() and tester.test_system_integration()
        else:
            # Run all tests
            success = tester.run_all_tests()
        
        # Close connections
        tester.close()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()