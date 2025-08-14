#!/usr/bin/env python3
"""
NYT News to Dgraph Knowledge Graph Importer

This script imports New York Times articles from JSON files into a Dgraph knowledge graph,
generating AI embeddings for semantic search capabilities.
"""

import os
import sys
import json
import uuid
import re
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path
from tqdm import tqdm
import pydgraph
from dotenv import load_dotenv

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dgraph_config import load_dgraph_config
from ai_provider import get_ai_provider

# Load environment variables
load_dotenv()

class NewsImporter:
    """Main class for importing news articles into Dgraph"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize the importer with configuration"""
        self.config = load_dgraph_config(config_file)
        self.dgraph_client = self._create_dgraph_client()
        self.ai_provider = get_ai_provider()
        
        # Configuration from environment
        self.batch_size = int(os.getenv('BATCH_SIZE', '100'))
        self.data_dir = os.getenv('DATA_DIR', 'data/articles')
        self.embedding_batch_size = int(os.getenv('EMBEDDING_BATCH_SIZE', '50'))
        
        print(f"🔧 Configuration loaded:")
        print(f"  Batch size: {self.batch_size}")
        print(f"  Data directory: {self.data_dir}")
        print(f"  Embedding batch size: {self.embedding_batch_size}")
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
    
    def _escape_string(self, s: str) -> str:
        """Escape special characters in strings for N-Quads"""
        if not isinstance(s, str):
            s = str(s)
        return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
    
    def _parse_byline(self, byline: str) -> List[str]:
        """Extract author names from byline like 'By Author1, Author2 and Author3'"""
        if not byline or not isinstance(byline, str):
            return []
        
        # Remove "By " prefix
        if byline.startswith("By "):
            byline = byline[3:]
        
        # Split by commas and 'and'
        authors = re.split(r',\s*|\s+and\s+', byline)
        return [author.strip() for author in authors if author.strip()]
    
    def _trim_all_whitespace(self, text: str) -> str:
        """Remove all whitespace and special characters for UID generation"""
        no_whitespace = ''.join(text.split())
        clean_text = re.sub(r'[^a-zA-Z0-9]', '', no_whitespace)
        return clean_text
    
    def _geocode_location(self, location: str) -> Optional[str]:
        """Geocode a location string to GeoJSON coordinates"""
        try:
            # Use AI provider to geocode (simplified approach)
            # In a real implementation, you might use a proper geocoding service
            prompt = f"Convert this location to coordinates: {location}. Return only JSON with lat and lon."
            response = self.ai_provider.chat_completion([
                {"role": "system", "content": "You are a geocoding assistant. Return only valid JSON with latitude and longitude."},
                {"role": "user", "content": prompt}
            ])
            
            # Try to extract coordinates from response
            # This is a simplified approach - in production use a proper geocoding service
            return None
        except Exception as e:
            print(f"⚠️  Geocoding failed for '{location}': {e}")
            return None
    
    def _generate_embedding(self, text: str) -> Optional[str]:
        """Generate AI embedding for text"""
        try:
            if not text or len(text.strip()) < 10:
                return None
            
            embedding = self.ai_provider.generate_embedding(text)
            return json.dumps(embedding)
        except Exception as e:
            print(f"⚠️  Embedding generation failed: {e}")
            return None
    
    def _article_to_nquads(self, article: Dict[str, Any]) -> List[str]:
        """Convert a single article to N-Quads format"""
        nquads = []
        article_uid = f"_:Article_{article.get('id', str(uuid.uuid4()))}"
        
        # Article basic info
        nquads.append(f'{article_uid} <dgraph.type> "Article" .')
        
        if "title" in article:
            nquads.append(f'{article_uid} <Article.title> "{self._escape_string(article["title"])}" .')
        
        if "abstract" in article:
            abstract = article["abstract"]
            nquads.append(f'{article_uid} <Article.abstract> "{self._escape_string(abstract)}" .')
            
            # Generate embedding for abstract
            embedding = self._generate_embedding(abstract)
            if embedding:
                nquads.append(f'{article_uid} <Article.embedding> "{embedding}" .')
        
        if "uri" in article:
            nquads.append(f'{article_uid} <Article.uri> "{self._escape_string(article["uri"])}" .')
        
        if "url" in article:
            nquads.append(f'{article_uid} <Article.url> "{self._escape_string(article["url"])}" .')
        
        if "published_date" in article:
            nquads.append(f'{article_uid} <Article.published> "{article["published_date"]}"^^<xs:dateTime> .')
        
        # Authors
        if "byline" in article:
            authors = self._parse_byline(article["byline"])
            for author_name in authors:
                author_uid = f"_:Author_{self._trim_all_whitespace(author_name)}"
                nquads.append(f'{author_uid} <dgraph.type> "Author" .')
                nquads.append(f'{author_uid} <Author.name> "{self._escape_string(author_name)}" .')
                nquads.append(f'{author_uid} <Author.article> {article_uid} .')
        
        # Topics (des_facet)
        if "des_facet" in article and isinstance(article["des_facet"], list):
            for topic in article["des_facet"]:
                topic_uid = f"_:Topic_{self._trim_all_whitespace(topic)}"
                nquads.append(f'{topic_uid} <dgraph.type> "Topic" .')
                nquads.append(f'{topic_uid} <Topic.name> "{self._escape_string(topic)}" .')
                nquads.append(f'{article_uid} <Article.topic> {topic_uid} .')
        
        # Organizations (org_facet)
        if "org_facet" in article and isinstance(article["org_facet"], list):
            for org in article["org_facet"]:
                org_uid = f"_:Organization_{self._trim_all_whitespace(org)}"
                nquads.append(f'{org_uid} <dgraph.type> "Organization" .')
                nquads.append(f'{org_uid} <Organization.name> "{self._escape_string(org)}" .')
                nquads.append(f'{article_uid} <Article.org> {org_uid} .')
        
        # People (per_facet)
        if "per_facet" in article and isinstance(article["per_facet"], list):
            for person in article["per_facet"]:
                person_uid = f"_:Person_{self._trim_all_whitespace(person)}"
                nquads.append(f'{person_uid} <dgraph.type> "Person" .')
                nquads.append(f'{person_uid} <Person.name> "{self._escape_string(person)}" .')
                nquads.append(f'{article_uid} <Article.person> {person_uid} .')
        
        # Geo locations (geo_facet)
        if "geo_facet" in article and isinstance(article["geo_facet"], list):
            for geo in article["geo_facet"]:
                geo_uid = f"_:Geo_{self._trim_all_whitespace(geo)}"
                nquads.append(f'{geo_uid} <dgraph.type> "Geo" .')
                nquads.append(f'{geo_uid} <Geo.name> "{self._escape_string(geo)}" .')
                
                # Try to geocode the location
                geojson = self._geocode_location(geo)
                if geojson:
                    nquads.append(f'{geo_uid} <Geo.location> "{geojson}"^^<geo:geojson> .')
                
                nquads.append(f'{article_uid} <Article.geo> {geo_uid} .')
        
        # Images
        if "media" in article and isinstance(article["media"], list):
            for media_item in article["media"]:
                if media_item.get("type") == "image":
                    image_uid = f"_:{uuid.uuid4()}"
                    nquads.append(f'{image_uid} <dgraph.type> "Image" .')
                    
                    if "caption" in media_item:
                        nquads.append(f'{image_uid} <Image.caption> "{self._escape_string(media_item["caption"])}" .')
                    
                    # Get the first image URL from metadata
                    if "media-metadata" in media_item and isinstance(media_item["media-metadata"], list) and len(media_item["media-metadata"]) > 0:
                        url = media_item["media-metadata"][0].get("url", "")
                        nquads.append(f'{image_uid} <Image.url> "{self._escape_string(url)}" .')
                    
                    nquads.append(f'{image_uid} <Image.article> {article_uid} .')
        
        return nquads
    
    def _process_json_files(self, directory: str) -> List[Dict[str, Any]]:
        """Process JSON files in the specified directory"""
        all_articles = []
        data_path = Path(directory)
        
        if not data_path.exists():
            print(f"❌ Data directory does not exist: {directory}")
            return all_articles
        
        json_files = list(data_path.glob("**/*.json"))
        print(f"📁 Found {len(json_files)} JSON files in {directory}")
        
        for json_file in tqdm(json_files, desc="Reading JSON files"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle different JSON structures
                    if isinstance(data.get("results"), list):
                        all_articles.extend(data.get("results"))
                    elif isinstance(data, dict):
                        if "response" in data and "docs" in data["response"]:
                            all_articles.extend(data["response"]["docs"])
                        else:
                            # Single article
                            all_articles.append(data)
            except json.JSONDecodeError as e:
                print(f"⚠️  Error parsing {json_file}: {e}")
            except Exception as e:
                print(f"⚠️  Error reading {json_file}: {e}")
        
        print(f"📊 Total articles found: {len(all_articles)}")
        return all_articles
    
    def _import_batch(self, nquads: List[str]) -> bool:
        """Import a batch of N-Quads into Dgraph"""
        try:
            # Join all N-Quads into a single string
            nquads_text = "\n".join(nquads)
            
            # Create transaction and mutate
            txn = self.dgraph_client.txn()
            response = txn.mutate(set_nquads=nquads_text)
            txn.commit()
            
            return True
        except Exception as e:
            print(f"❌ Batch import failed: {e}")
            return False
    
    def import_articles(self, directory: Optional[str] = None, output_file: Optional[str] = None) -> bool:
        """Main method to import articles from JSON files"""
        if directory is None:
            directory = self.data_dir
        
        print(f"🚀 Starting import from: {directory}")
        
        # Process JSON files
        articles = self._process_json_files(directory)
        if not articles:
            print("❌ No articles found to import")
            return False
        
        # Convert to N-Quads
        print("🔄 Converting articles to N-Quads format...")
        all_nquads = []
        
        for article in tqdm(articles, desc="Converting articles"):
            try:
                article_nquads = self._article_to_nquads(article)
                all_nquads.extend(article_nquads)
            except Exception as e:
                print(f"⚠️  Error converting article: {e}")
                continue
        
        print(f"📝 Generated {len(all_nquads)} N-Quads")
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(all_nquads))
                print(f"💾 Saved N-Quads to: {output_file}")
            except Exception as e:
                print(f"⚠️  Failed to save to file: {e}")
        
        # Import to Dgraph in batches
        print("📤 Importing to Dgraph...")
        success_count = 0
        total_batches = (len(all_nquads) + self.batch_size - 1) // self.batch_size
        
        for i in tqdm(range(0, len(all_nquads), self.batch_size), total=total_batches, desc="Importing batches"):
            batch = all_nquads[i:i + self.batch_size]
            if self._import_batch(batch):
                success_count += len(batch)
            else:
                print(f"⚠️  Failed to import batch {i//self.batch_size + 1}")
        
        print(f"✅ Import complete! Successfully imported {success_count} N-Quads")
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Import NYT articles into Dgraph knowledge graph')
    parser.add_argument('--config', default='config.env', help='Configuration file path')
    parser.add_argument('--data-dir', help='Data directory containing JSON files')
    parser.add_argument('--output', help='Output file for N-Quads (optional)')
    parser.add_argument('--batch-size', type=int, help='Batch size for imports')
    parser.add_argument('--embedding-batch-size', type=int, help='Batch size for embeddings')
    
    args = parser.parse_args()
    
    try:
        # Create importer
        importer = NewsImporter(args.config)
        
        # Override configuration if provided
        if args.batch_size:
            importer.batch_size = args.batch_size
        if args.embedding_batch_size:
            importer.embedding_batch_size = args.embedding_batch_size
        
        # Start import
        success = importer.import_articles(
            directory=args.data_dir,
            output_file=args.output
        )
        
        if success:
            print("🎉 News import completed successfully!")
            sys.exit(0)
        else:
            print("❌ News import failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
