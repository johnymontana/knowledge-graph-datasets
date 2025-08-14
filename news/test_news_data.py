#!/usr/bin/env python3
"""
Test News Knowledge Graph Data and Configuration

This script validates the news knowledge graph configuration, connection,
and data integrity.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dgraph_config import load_dgraph_config
from ai_provider import get_ai_provider

# Load environment variables
load_dotenv()

class NewsDataValidator:
    """Class for validating news knowledge graph data and configuration"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize the validator"""
        self.config = load_dgraph_config(config_file)
        self.ai_provider = None
        
        print(f"🔧 Configuration loaded for validation")
    
    def test_configuration(self) -> bool:
        """Test the configuration settings"""
        print("\n" + "="*60)
        print("🔧 CONFIGURATION VALIDATION")
        print("="*60)
        
        success = True
        
        # Test Dgraph configuration
        print("\n1. Testing Dgraph configuration...")
        try:
            if self.config.validate_connection():
                print("✅ Dgraph configuration is valid")
                self.config.print_config()
            else:
                print("❌ Dgraph configuration has issues")
                success = False
        except Exception as e:
            print(f"❌ Dgraph configuration test failed: {e}")
            success = False
        
        # Test AI provider configuration
        print("\n2. Testing AI provider configuration...")
        try:
            self.ai_provider = get_ai_provider()
            print(f"✅ AI provider initialized: {self.ai_provider.__class__.__name__}")
        except Exception as e:
            print(f"❌ AI provider initialization failed: {e}")
            success = False
        
        # Test environment variables
        print("\n3. Testing environment variables...")
        env_vars = [
            'DGRAPH_CONNECTION_STRING',
            'BATCH_SIZE',
            'DATA_DIR',
            'EMBEDDING_BATCH_SIZE'
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                print(f"✅ {var}: {value}")
            else:
                print(f"⚠️  {var}: Not set (using default)")
        
        # Test AI API keys
        print("\n4. Testing AI API keys...")
        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        if openai_key:
            print(f"✅ OPENAI_API_KEY: {'*' * 10}{openai_key[-4:]}")
        else:
            print("⚠️  OPENAI_API_KEY: Not set")
        
        if anthropic_key:
            print(f"✅ ANTHROPIC_API_KEY: {'*' * 10}{anthropic_key[-4:]}")
        else:
            print("⚠️  ANTHROPIC_API_KEY: Not set")
        
        if not openai_key and not anthropic_key:
            print("ℹ️  No cloud API keys found, will use Ollama if available")
        
        return success
    
    def test_dgraph_connection(self) -> bool:
        """Test the Dgraph connection"""
        print("\n" + "="*60)
        print("🔌 DGRAPH CONNECTION TEST")
        print("="*60)
        
        success = True
        
        try:
            # Test gRPC connection
            print("\n1. Testing gRPC connection...")
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
            
            # Test basic query
            query = """
            {
              health(func: type(Article), first: 1) {
                uid
                Article.title
              }
            }
            """
            
            try:
                res = dgraph_client.txn(read_only=True).query(query)
                print("✅ gRPC connection successful")
                print("✅ Basic query executed successfully")
                
                # Check if we have data
                results = json.loads(res.json)
                if results.get('data', {}).get('health'):
                    print("✅ Knowledge graph contains data")
                else:
                    print("⚠️  Knowledge graph appears to be empty")
                
            except Exception as e:
                print(f"❌ Basic query failed: {e}")
                success = False
            
        except ImportError:
            print("⚠️  pydgraph not available, testing HTTP connection...")
            success = self._test_http_connection()
        except Exception as e:
            print(f"❌ gRPC connection failed: {e}")
            success = False
        
        return success
    
    def _test_http_connection(self) -> bool:
        """Test HTTP connection to Dgraph"""
        try:
            import requests
            
            url = f"{self.config.get_http_url()}/query"
            headers = self.config.get_headers()
            
            # Test basic query
            payload = {
                "query": """
                {
                  health(func: type(Article), first: 1) {
                    uid
                    Article.title
                  }
                }
                """
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            print("✅ HTTP connection successful")
            print("✅ Basic query executed successfully")
            
            # Check if we have data
            results = response.json()
            if results.get('data', {}).get('health'):
                print("✅ Knowledge graph contains data")
            else:
                print("⚠️  Knowledge graph appears to be empty")
            
            return True
            
        except Exception as e:
            print(f"❌ HTTP connection failed: {e}")
            return False
    
    def test_ai_provider(self) -> bool:
        """Test the AI provider"""
        print("\n" + "="*60)
        print("🧠 AI PROVIDER TEST")
        print("="*60)
        
        if not self.ai_provider:
            print("❌ AI provider not initialized")
            return False
        
        success = True
        
        try:
            # Test embedding generation
            print("\n1. Testing embedding generation...")
            test_text = "This is a test text for embedding generation."
            embedding = self.ai_provider.generate_embedding(test_text)
            
            if embedding and isinstance(embedding, list) and len(embedding) > 0:
                print(f"✅ Embedding generated successfully: {len(embedding)} dimensions")
                print(f"   Sample values: {embedding[:3]}...")
            else:
                print("❌ Embedding generation failed")
                success = False
            
            # Test chat completion if available
            print("\n2. Testing chat completion...")
            try:
                messages = [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say hello in one word."}
                ]
                
                response = self.ai_provider.chat_completion(messages)
                if response and len(response.strip()) > 0:
                    print(f"✅ Chat completion successful: '{response.strip()}'")
                else:
                    print("❌ Chat completion failed")
                    success = False
                    
            except NotImplementedError:
                print("ℹ️  Chat completion not supported by this provider")
            except Exception as e:
                print(f"❌ Chat completion failed: {e}")
                success = False
            
        except Exception as e:
            print(f"❌ AI provider test failed: {e}")
            success = False
        
        return success
    
    def test_data_directory(self) -> bool:
        """Test the data directory structure"""
        print("\n" + "="*60)
        print("📁 DATA DIRECTORY TEST")
        print("="*60)
        
        success = True
        data_dir = os.getenv('DATA_DIR', 'data/articles')
        
        print(f"\n1. Testing data directory: {data_dir}")
        
        if not os.path.exists(data_dir):
            print(f"❌ Data directory does not exist: {data_dir}")
            return False
        
        # Check for JSON files
        json_files = []
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))
        
        if json_files:
            print(f"✅ Found {len(json_files)} JSON files")
            
            # Test reading a few files
            print("\n2. Testing JSON file reading...")
            test_count = min(3, len(json_files))
            for i, json_file in enumerate(json_files[:test_count]):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Check structure
                    if isinstance(data, dict):
                        if 'results' in data and isinstance(data['results'], list):
                            print(f"   ✅ {os.path.basename(json_file)}: {len(data['results'])} articles")
                        elif 'response' in data and 'docs' in data['response']:
                            print(f"   ✅ {os.path.basename(json_file)}: {len(data['response']['docs'])} articles")
                        else:
                            print(f"   ✅ {os.path.basename(json_file)}: Single article")
                    else:
                        print(f"   ⚠️  {os.path.basename(json_file)}: Unexpected format")
                        
                except Exception as e:
                    print(f"   ❌ {os.path.basename(json_file)}: Error reading - {e}")
                    success = False
        else:
            print("⚠️  No JSON files found in data directory")
        
        return success
    
    def test_schema(self) -> bool:
        """Test the Dgraph schema"""
        print("\n" + "="*60)
        print("📋 SCHEMA TEST")
        print("="*60)
        
        success = True
        
        try:
            # Test schema query
            print("\n1. Testing schema query...")
            import pydgraph
            
            # Create gRPC channel
            channel_options = [
                ('grpc.max_send_message_length', 50 * 1024 * 1024),
                ('grpc.max_receive_message_length', 50 * 1024 * 1024),
                ('grpc.max_metadata_size', 32 * 1024)
            ]
            
            client_stub = pydgraph.DgraphClientStub(
                self.config.get_grpc_url(), 
                options=channel_options
            )
            dgraph_client = pydgraph.DgraphClient(client_stub)
            
            # Query schema
            schema_query = """
            schema {
              type
            }
            """
            
            try:
                res = dgraph_client.txn(read_only=True).query(schema_query)
                schema_data = json.loads(res.json)
                
                if schema_data.get('data', {}).get('schema'):
                    print("✅ Schema query successful")
                    
                    # Check for expected types
                    schema = schema_data['data']['schema']
                    expected_types = ['Article', 'Topic', 'Organization', 'Person', 'Geo', 'Author', 'Image']
                    
                    found_types = []
                    for item in schema:
                        if 'type' in item:
                            found_types.append(item['type'])
                    
                    print(f"   Found types: {', '.join(found_types)}")
                    
                    missing_types = [t for t in expected_types if t not in found_types]
                    if missing_types:
                        print(f"   ⚠️  Missing expected types: {', '.join(missing_types)}")
                    else:
                        print("   ✅ All expected types found")
                        
                else:
                    print("⚠️  Schema appears to be empty")
                    
            except Exception as e:
                print(f"❌ Schema query failed: {e}")
                success = False
                
        except ImportError:
            print("⚠️  pydgraph not available, skipping schema test")
        except Exception as e:
            print(f"❌ Schema test failed: {e}")
            success = False
        
        return success
    
    def run_all_tests(self) -> bool:
        """Run all validation tests"""
        print("🚀 Running all validation tests for News Knowledge Graph")
        print("="*80)
        
        all_success = True
        
        # Run tests
        if not self.test_configuration():
            all_success = False
        
        if not self.test_dgraph_connection():
            all_success = False
        
        if not self.test_ai_provider():
            all_success = False
        
        if not self.test_data_directory():
            all_success = False
        
        if not self.test_schema():
            all_success = False
        
        # Summary
        print("\n" + "="*80)
        if all_success:
            print("🎉 All validation tests passed!")
        else:
            print("❌ Some validation tests failed. Please check the issues above.")
        
        return all_success

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Validate news knowledge graph data and configuration')
    parser.add_argument('--config', default='config.env', help='Configuration file path')
    parser.add_argument('--config-only', action='store_true', help='Test only configuration')
    parser.add_argument('--connection-only', action='store_true', help='Test only Dgraph connection')
    parser.add_argument('--ai-only', action='store_true', help='Test only AI provider')
    parser.add_argument('--data-only', action='store_true', help='Test only data directory')
    parser.add_argument('--schema-only', action='store_true', help='Test only schema')
    
    args = parser.parse_args()
    
    try:
        # Create validator
        validator = NewsDataValidator(args.config)
        
        # Run specific tests or all
        if args.config_only:
            success = validator.test_configuration()
        elif args.connection_only:
            success = validator.test_dgraph_connection()
        elif args.ai_only:
            success = validator.test_ai_provider()
        elif args.data_only:
            success = validator.test_data_directory()
        elif args.schema_only:
            success = validator.test_schema()
        else:
            # Run all tests
            success = validator.run_all_tests()
        
        if success:
            print("\n✅ Validation completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Validation completed with issues!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
